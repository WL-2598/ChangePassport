"""Minimal GitHub REST collector for PR, commit, review and check facts.

Only the GitHub REST API is contacted, and only when ``collect()`` is called
without an offline snapshot. The token is read from an environment variable and
is never logged, echoed, or written into the evidence packet.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MAX_PAGES = 10
TIMEOUT_SECONDS = 15
DEFAULT_API_BASE = "https://api.github.com"


class CollectorError(RuntimeError):
    """Raised for invalid snapshots or GitHub API failures."""


def _utcnow() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _validate_api_base(api_base: str) -> str:
    parsed = urllib.parse.urlparse(api_base)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise CollectorError("GitHub API base must be an https URL without credentials")
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise CollectorError("GitHub API base must not contain a path, query or fragment")
    return api_base.rstrip("/")


def _same_origin(base: str, url: str) -> bool:
    first = urllib.parse.urlparse(base)
    second = urllib.parse.urlparse(url)
    return first.scheme == second.scheme and first.netloc == second.netloc


def load_snapshot(path: Path) -> dict[str, Any]:
    """Load a previously captured (possibly synthetic) JSON snapshot offline."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CollectorError(f"snapshot not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CollectorError(f"invalid JSON in snapshot {path}: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise CollectorError("snapshot must be a JSON object")
    for key in ("commits", "reviews", "check_runs", "statuses"):
        if not isinstance(data.get(key, []), list):
            raise CollectorError(f"snapshot.{key} must be a list")
    source = data.setdefault("source", {})
    if not isinstance(source, dict):
        raise CollectorError("snapshot.source must be an object")
    # A file snapshot is never proof of a live API call, even if it contains
    # URLs that look like GitHub responses.
    source["kind"] = "snapshot"
    return data


class GitHubCollector:
    def __init__(
        self,
        token: str | None = None,
        api_base: str | None = None,
        opener: Any = None,
    ) -> None:
        self.api_base = _validate_api_base(
            api_base or os.environ.get("GITHUB_API_URL", DEFAULT_API_BASE)
        )
        self.token = token
        self._urlopen = opener or urllib.request.urlopen
        self.collection_errors: list[dict[str, str]] = []
        self.pagination_truncated = False

    def _get_all(self, path: str, list_key: str | None = None) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        url: str | None = self.api_base + path
        for _ in range(MAX_PAGES):
            if url is None:
                self.pagination_truncated = True
                break
            if not _same_origin(self.api_base, url):
                raise CollectorError("refusing to follow a pagination link outside the GitHub API")
            request = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "changepassport/0.1",
                    "X-GitHub-Api-Version": "2022-11-28",
                    **({"Authorization": f"Bearer {self.token}"} if self.token else {}),
                },
            )
            try:
                with self._urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                    link = response.headers.get("Link", "")
            except urllib.error.HTTPError as exc:
                # A missing permission must not break the report; it becomes a gap.
                self.collection_errors.append({"path": path, "status": str(exc.code)})
                return items
            except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
                raise CollectorError(
                    f"GitHub API request failed for {path}: {type(exc).__name__}"
                ) from exc
            if isinstance(payload, dict) and list_key and isinstance(payload.get(list_key), list):
                # check-runs is wrapped in {"total_count": n, "check_runs": [...]}.
                payload = payload[list_key]
            elif isinstance(payload, dict) and "message" in payload and "url" not in payload:
                # An API error must not abort the whole packet; record it as a gap.
                self.collection_errors.append(
                    {"path": path, "status": str(payload.get("message", "api_error"))[:80]}
                )
                return items
            if not isinstance(payload, list):
                raise CollectorError(f"unexpected GitHub API response for {path}")
            items.extend(item for item in payload if isinstance(item, dict))
            url = next(
                (
                    part.strip().split(">")[0][1:]
                    for part in link.split(",")
                    if 'rel="next"' in part and part.strip().startswith("<")
                ),
                None,
            )
        if url is not None:
            self.pagination_truncated = True
        return items

    def _get_one(self, path: str) -> dict[str, Any] | None:
        url = self.api_base + path
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "changepassport/0.1",
                "X-GitHub-Api-Version": "2022-11-28",
                **({"Authorization": f"Bearer {self.token}"} if self.token else {}),
            },
        )
        try:
            with self._urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            # Do not include headers or response bodies: they may carry tokens.
            self.collection_errors.append({"path": path, "status": str(exc.code)})
            return None
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
            raise CollectorError(
                f"GitHub API request failed for {path}: {type(exc).__name__}"
            ) from exc
        if not isinstance(payload, dict):
            raise CollectorError(f"unexpected GitHub API response for {path}")
        return payload

    def collect(
        self,
        owner: str,
        name: str,
        pull_request: int | str,
        commit_sha: str,
    ) -> dict[str, Any]:
        """Collect only the fact types listed in the product charter."""
        repo = f"/repos/{owner}/{name}"
        pr = (
            self._get_one(f"{repo}/pulls/{pull_request}") if isinstance(pull_request, int) else None
        )
        head_sha = ""
        if pr:
            head = pr.get("head") or {}
            head_sha = str(head.get("sha") or "")
        elif commit_sha != "missing":
            head_sha = commit_sha

        if pr:
            commits = self._get_all(f"{repo}/pulls/{pull_request}/commits?per_page=100")
            reviews = self._get_all(f"{repo}/pulls/{pull_request}/reviews?per_page=100")
        else:
            maybe_commit = self._get_one(f"{repo}/commits/{commit_sha}") if head_sha else None
            commits = [maybe_commit] if isinstance(maybe_commit, dict) else []
            reviews = []

        check_runs = (
            self._get_all(
                f"{repo}/commits/{head_sha}/check-runs?per_page=100", list_key="check_runs"
            )
            if head_sha
            else []
        )
        statuses = (
            self._get_all(f"{repo}/commits/{head_sha}/statuses?per_page=100") if head_sha else []
        )

        return {
            "source": {
                "kind": "github_api",
                "repository_url": f"https://github.com/{owner}/{name}",
                "collected_at": _utcnow(),
                "api_base": self.api_base,
            },
            "pagination_truncated": self.pagination_truncated,
            "collection_errors": list(self.collection_errors),
            "pull_request": pr,
            "commits": commits,
            "reviews": reviews,
            "check_runs": check_runs,
            "statuses": statuses,
        }

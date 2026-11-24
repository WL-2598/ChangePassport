import json
from pathlib import Path
from typing import Any

import pytest

from changepassport.collectors.github import CollectorError, GitHubCollector, load_snapshot

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


class FakeResponse:
    def __init__(self, payload: Any, headers: dict[str, str] | None = None) -> None:
        self.payload = payload
        self.headers = headers or {}
        self.body = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> bool:
        return False

    def read(self) -> bytes:
        return self.body


def test_load_snapshot_never_claims_live_api() -> None:
    snapshot = load_snapshot(FIXTURES / "snapshot.json")
    assert snapshot["source"]["kind"] == "snapshot"
    assert snapshot["source"]["collected_at"] == "2026-01-15T10:00:00Z"


def test_snapshot_rejects_wrong_shape(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"reviews": "not-a-list"}), encoding="utf-8")
    with pytest.raises(CollectorError, match="reviews must be a list"):
        load_snapshot(bad)


def test_collector_talks_only_to_configured_github_api() -> None:
    seen: list[tuple[str, dict[str, str]]] = []

    def opener(request: Any, timeout: int) -> FakeResponse:
        assert timeout > 0
        seen.append((request.full_url, dict(request.headers)))
        if request.full_url.endswith("/pulls/42"):
            return FakeResponse(
                {"html_url": "https://github.com/a/b/pull/42", "head": {"sha": "abc"}}, {}
            )
        return FakeResponse([{"name": "unit-tests", "conclusion": "success"}])

    collector = GitHubCollector(token="secret-token", opener=opener)
    snapshot = collector.collect("a", "b", 42, "missing")
    assert all(url.startswith("https://api.github.com/repos/a/b") for url, _ in seen)
    assert seen[0][1]["Authorization"] == "Bearer secret-token"
    assert snapshot["source"]["kind"] == "github_api"
    assert "secret-token" not in json.dumps(snapshot)


@pytest.mark.parametrize(
    "base",
    ["http://api.github.com", "https://user:pass@api.github.com", "https://api.github.com/path"],
)
def test_collector_rejects_unsafe_api_base(base: str) -> None:
    with pytest.raises(CollectorError, match="GitHub API base"):
        GitHubCollector(api_base=base)


def test_collector_rejects_external_pagination_link() -> None:
    def opener(request: Any, timeout: int) -> FakeResponse:
        if request.full_url.endswith("/pulls/42"):
            return FakeResponse({"head": {"sha": "abc"}})
        return FakeResponse([], {"Link": '<https://evil.example/next>; rel="next"'})

    collector = GitHubCollector(opener=opener)
    with pytest.raises(CollectorError, match="outside the GitHub API"):
        collector.collect("a", "b", 42, "missing")

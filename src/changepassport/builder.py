"""Build a passport from a config plus a captured/synthetic fact snapshot.

The builder never invents a fact. Absent values are the literal string
``missing`` and are listed in ``completeness.missing`` with an expected source.
"""

from __future__ import annotations

from typing import Any

from changepassport import __version__
from changepassport.config import MISSING, UNKNOWN
from changepassport.verify import compute_digest

SCHEMA_VERSION = "1.0.0"


def _text(value: Any) -> str:
    if value is None or value == "":
        return MISSING
    return str(value)


def _source_kind(snapshot: dict[str, Any]) -> str:
    kind = _text((snapshot.get("source") or {}).get("kind"))
    return kind if kind in {"github_api", "snapshot"} else "snapshot"


def _collect_reviews(
    snapshot: dict[str, Any], source_kind: str
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    reviews: list[dict[str, str]] = []
    approvals: list[dict[str, str]] = []
    for review in snapshot.get("reviews", []):
        if not isinstance(review, dict):
            continue
        state = _text(review.get("state")).lower()
        item = {
            "reviewer": _text((review.get("user") or {}).get("login")),
            "state": state if state else MISSING,
            "submitted_at": _text(review.get("submitted_at")),
            "source_url": _text(review.get("html_url") or review.get("url")),
            "source": source_kind,
        }
        reviews.append(item)
        if state == "approved":
            approvals.append(
                {
                    "reviewer": item["reviewer"],
                    "approved_at": item["submitted_at"],
                    "source_url": item["source_url"],
                    "source": source_kind,
                }
            )
    return reviews, approvals


def _collect_checks(snapshot: dict[str, Any], source_kind: str) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    for run in snapshot.get("check_runs", []):
        if not isinstance(run, dict):
            continue
        status = _text(run.get("status")).lower()
        conclusion = _text(run.get("conclusion")).lower()
        if conclusion == MISSING and status and status != "completed":
            conclusion = status
        checks.append(
            {
                "name": _text(run.get("name")),
                "conclusion": conclusion if conclusion else MISSING,
                "completed_at": _text(run.get("completed_at")),
                "source_url": _text(run.get("html_url") or run.get("details_url")),
                "source": source_kind,
            }
        )
    for item in snapshot.get("statuses", []):
        if not isinstance(item, dict):
            continue
        checks.append(
            {
                "name": _text(item.get("context")),
                "conclusion": _text(item.get("state")).lower(),
                "completed_at": _text(item.get("updated_at")),
                "source_url": _text(item.get("target_url")),
                "source": source_kind,
            }
        )
    return checks


def _missing_entry(field: str, reason: str, expected_source: str) -> dict[str, str]:
    return {"field": field, "reason": reason, "expected_source": expected_source}


def build_passport(
    config: dict[str, Any],
    snapshot: dict[str, Any],
    generated_at: str,
    generator_version: str = __version__,
) -> dict[str, Any]:
    """Build a deterministic passport. Same inputs always yield the same digest."""
    source_kind = _source_kind(snapshot)
    repository = config["repository"]
    declared = config["declared"]
    pr = snapshot.get("pull_request")
    pr = pr if isinstance(pr, dict) else None
    pr_number = config["change"].get("pull_request", MISSING)
    sha_from_config = _text(config["change"].get("commit_sha"))
    head_sha = _text((pr.get("head") or {}).get("sha")) if pr else sha_from_config
    if head_sha == MISSING and snapshot.get("commits"):
        first = snapshot["commits"][0]
        if isinstance(first, dict):
            head_sha = _text(first.get("sha"))

    commit_shas = [
        _text(item.get("sha"))
        for item in snapshot.get("commits", [])
        if isinstance(item, dict) and _text(item.get("sha")) != MISSING
    ]
    reviews, approvals = _collect_reviews(snapshot, source_kind)
    checks = _collect_checks(snapshot, source_kind)

    change_id = (
        f"PR #{pr_number}"
        if isinstance(pr_number, int)
        else (head_sha if head_sha != MISSING else MISSING)
    )
    change_url = _text(pr.get("html_url")) if pr else MISSING
    if change_url == MISSING and head_sha != MISSING:
        change_url = (
            f"https://github.com/{repository['owner']}/{repository['name']}/commit/{head_sha}"
        )

    ticket = declared.get("external_ticket") or {}
    ticket_reference = _text(ticket.get("reference"))
    ticket_url = _text(ticket.get("url"))
    rollback_plan = declared.get("rollback_plan") or {}

    deployments: list[dict[str, str]] = []
    for item in declared.get("deployments", []):
        if isinstance(item, dict):
            deployments.append(
                {
                    "environment": _text(item.get("environment")),
                    "deployed_at": _text(item.get("deployed_at")),
                    "actor": _text(item.get("actor")),
                    "status": _text(item.get("status")),
                    "source_url": _text(item.get("source_url")),
                    "source": "declared",
                }
            )
    rollbacks: list[dict[str, str]] = []
    for item in declared.get("rollbacks", []):
        if isinstance(item, dict):
            rollbacks.append(
                {
                    "environment": _text(item.get("environment")),
                    "rolled_back_at": _text(item.get("rolled_back_at")),
                    "actor": _text(item.get("actor")),
                    "notes": _text(item.get("notes")),
                    "source_url": _text(item.get("source_url")),
                    "source": "declared",
                }
            )
    exceptions: list[dict[str, str]] = []
    for item in declared.get("exceptions", []):
        if isinstance(item, dict):
            exceptions.append(
                {
                    "type": _text(item.get("type")),
                    "description": _text(item.get("description")),
                    "approved_by": _text(item.get("approved_by")),
                    "source_url": _text(item.get("source_url")),
                    "source": "declared",
                }
            )

    passport: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generator": {
            "name": "changepassport",
            "version": generator_version,
            "generated_at": generated_at,
        },
        "repository": {
            "owner": repository["owner"],
            "name": repository["name"],
            "url": _text(repository.get("url")),
            "default_branch": _text((pr.get("base") or {}).get("ref")) if pr else UNKNOWN,
        },
        "policy": {
            "id": _text(config["policy"].get("id")),
            "required": list(config["policy"]["require"]),
        },
        "change": {
            "id": change_id,
            "kind": "pull_request" if isinstance(pr_number, int) else "commit",
            "title": _text(pr.get("title")) if pr else MISSING,
            "purpose": _text(declared.get("purpose")),
            "author": _text((pr.get("user") or {}).get("login")) if pr else MISSING,
            "merged_at": _text(pr.get("merged_at")) if pr else MISSING,
            "url": change_url,
            "head_sha": head_sha,
            "commit_shas": commit_shas,
            "external_ticket": {"reference": ticket_reference, "url": ticket_url},
        },
        "reviews": reviews,
        "approvals": approvals,
        "checks": checks,
        "deployments": deployments,
        "rollbacks": rollbacks,
        "rollback_plan": {
            "description": _text(rollback_plan.get("description")),
            "source_url": _text(rollback_plan.get("source_url")),
        },
        "exceptions": exceptions,
        "exception_review": {
            "status": "reviewed" if declared.get("exceptions_reviewed") is True else "not_reviewed",
            "source": "declared",
        },
        "completeness": {"missing": [], "unknown": []},
        "provenance": {},
        "content_digest": {"algorithm": "sha256", "value": ""},
    }

    missing = passport["completeness"]["missing"]
    if passport["change"]["title"] == MISSING:
        missing.append(_missing_entry("change.title", "没有从 GitHub 取到标题", source_kind))
    if passport["change"]["purpose"] == MISSING:
        missing.append(_missing_entry("change.purpose", "配置中未填写变更目的", "declared config"))
    if ticket_reference == MISSING or ticket_url == MISSING:
        missing.append(
            _missing_entry(
                "change.external_ticket", "配置中未填写外部工单编号或链接", "declared config"
            )
        )
    if passport["change"]["merged_at"] == MISSING:
        missing.append(
            _missing_entry(
                "change.merged_at", "没有可用的合并时间（commit 模式可为未知）", source_kind
            )
        )
    if not approvals:
        missing.append(_missing_entry("approvals", "没有 GitHub APPROVED 审核记录", source_kind))
    if not checks:
        missing.append(_missing_entry("checks", "没有取到 Check/Status 记录", source_kind))
    if not deployments:
        missing.append(_missing_entry("deployments", "人工未声明部署记录", "declared config"))
    if not rollbacks:
        missing.append(_missing_entry("rollbacks", "人工未声明回滚记录", "declared config"))
    if passport["rollback_plan"]["source_url"] == MISSING:
        missing.append(
            _missing_entry("rollback_plan", "人工未填写回滚说明或链接", "declared config")
        )
    if passport["exception_review"]["status"] != "reviewed":
        missing.append(
            _missing_entry("exception_review", "尚未人工确认例外披露", "declared config")
        )
    if snapshot.get("pagination_truncated"):
        missing.append(
            _missing_entry(
                "collector.pagination", "GitHub API 分页超过上限，数据可能不完整", source_kind
            )
        )
    for error in snapshot.get("collection_errors", []):
        if isinstance(error, dict):
            missing.append(
                _missing_entry(
                    "collector." + _text(error.get("path")),
                    "GitHub API 返回 HTTP " + _text(error.get("status")),
                    source_kind,
                )
            )

    passport["provenance"] = {
        "change.title": {
            "source": source_kind if passport["change"]["title"] != MISSING else MISSING,
            "url": change_url,
        },
        "change.purpose": {
            "source": "declared" if passport["change"]["purpose"] != MISSING else MISSING,
            "url": MISSING,
        },
        "change.external_ticket": {
            "source": "declared" if ticket_url != MISSING else MISSING,
            "url": ticket_url,
        },
        "approvals": {"source": source_kind if approvals else MISSING, "url": change_url},
        "checks": {"source": source_kind if checks else MISSING, "url": change_url},
        "deployments": {
            "source": "declared" if deployments else MISSING,
            "url": deployments[0]["source_url"] if deployments else MISSING,
        },
        "rollback_plan": {
            "source": "declared" if passport["rollback_plan"]["source_url"] != MISSING else MISSING,
            "url": passport["rollback_plan"]["source_url"],
        },
        "exception_review": {"source": "declared", "url": MISSING},
        "content_digest": {"source": "computed", "url": MISSING},
    }
    passport["completeness"]["unknown"] = [
        key
        for key, value in passport["provenance"].items()
        if value["source"] in {"unknown", MISSING}
    ]
    passport["content_digest"]["value"] = compute_digest(passport)
    return passport

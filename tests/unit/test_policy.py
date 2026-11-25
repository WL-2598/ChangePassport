import json
from pathlib import Path
from typing import Any

from changepassport.builder import build_passport
from changepassport.config import load_config
from changepassport.policy import evaluate

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def build(config_name: str, snapshot_name: str) -> dict[str, Any]:
    config = load_config(FIXTURES / config_name)
    snapshot = json.loads((FIXTURES / snapshot_name).read_text(encoding="utf-8"))
    return build_passport(config, snapshot, "2026-01-15T10:30:00Z")


def test_approval_uses_only_explicit_github_reviews() -> None:
    passport = build("config.json", "snapshot.json")
    assert [item["reviewer"] for item in passport["approvals"]] == ["reviewer-bob"]
    assert len(passport["reviews"]) == 2
    results = {
        item["id"]: item["status"] for item in evaluate(passport, passport["policy"]["required"])
    }
    assert set(results.values()) == {"pass"}


def test_missing_facts_become_visible_gaps() -> None:
    passport = build("config_missing.json", "snapshot_missing.json")
    assert passport["approvals"] == []
    assert passport["change"]["purpose"] == "missing"
    results = {item["id"]: item for item in evaluate(passport, passport["policy"]["required"])}
    assert results["purpose"]["status"] == "gap"
    assert results["approval"]["status"] == "gap"
    assert results["exception_disclosure"]["status"] == "gap"
    assert any(item["field"] == "checks" for item in passport["completeness"]["missing"])


def test_failing_check_is_a_gap() -> None:
    passport = build("config.json", "snapshot.json")
    passport["checks"][0]["conclusion"] = "failure"
    results = {item["id"]: item for item in evaluate(passport, passport["policy"]["required"])}
    assert results["successful_checks"]["status"] == "gap"
    assert "失败" in results["successful_checks"]["detail"]


def test_unknown_requirement_is_not_silently_passed() -> None:
    passport = build("config.json", "snapshot.json")
    assert evaluate(passport, ["not_a_real_check"])[0]["status"] == "gap"

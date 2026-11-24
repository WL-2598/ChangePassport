"""Deterministic policy checks. No model or judgement is involved."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

CHECK_NAMES = {
    "purpose": "变更目的已填写",
    "external_ticket": "外部工单链接已填写",
    "approval": "至少一条 GitHub 审批记录",
    "successful_checks": "至少一条成功的 Check，且无失败 Check",
    "deployment": "至少一条人工声明的部署记录",
    "rollback_plan": "回滚说明或链接已填写",
    "exception_disclosure": "已人工确认例外披露（含确认无例外）",
}
KNOWN_REQUIREMENTS = tuple(CHECK_NAMES)

FAILING_CONCLUSIONS = {"failure", "cancelled", "timed_out", "action_required"}
SUCCESS_CONCLUSIONS = {"success", "neutral", "skipped"}


def _obj(passport: dict[str, Any], key: str) -> dict[str, Any]:
    value = passport.get(key)
    return value if isinstance(value, dict) else {}


def _array(passport: dict[str, Any], key: str) -> list[Any]:
    value = passport.get(key)
    return value if isinstance(value, list) else []


def _purpose(passport: dict[str, Any]) -> str | None:
    if _obj(passport, "change").get("purpose", "missing") == "missing":
        return "change.purpose 为 missing"
    return None


def _external_ticket(passport: dict[str, Any]) -> str | None:
    ticket = _obj(_obj(passport, "change"), "external_ticket")
    if ticket.get("reference", "missing") == "missing" or ticket.get("url", "missing") == "missing":
        return "change.external_ticket 缺少编号或链接"
    return None


def _approval(passport: dict[str, Any]) -> str | None:
    if not _array(passport, "approvals"):
        return "没有从 GitHub Reviews 中取到审批记录（未推测审批）"
    return None


def _successful_checks(passport: dict[str, Any]) -> str | None:
    checks = _array(passport, "checks")
    if not checks:
        return "没有 Check 记录"
    conclusions = {
        str(check.get("conclusion", "missing")) if isinstance(check, dict) else "missing"
        for check in checks
    }
    if conclusions & FAILING_CONCLUSIONS:
        return "存在结论为失败/取消/超时的 Check"
    if not conclusions & SUCCESS_CONCLUSIONS:
        return "没有结论为成功的 Check"
    return None


def _deployment(passport: dict[str, Any]) -> str | None:
    for item in _array(passport, "deployments"):
        if (
            isinstance(item, dict)
            and item.get("environment", "missing") != "missing"
            and item.get("deployed_at", "missing") != "missing"
        ):
            return None
    return "没有含环境与时间的人工声明部署记录"


def _rollback_plan(passport: dict[str, Any]) -> str | None:
    if _obj(passport, "rollback_plan").get("source_url", "missing") == "missing":
        return "rollback_plan.source_url 为 missing"
    return None


def _exception_disclosure(passport: dict[str, Any]) -> str | None:
    if _obj(passport, "exception_review").get("status") != "reviewed":
        return "尚未人工确认例外披露状态"
    return None


_CHECKS: dict[str, Callable[[dict[str, Any]], str | None]] = {
    "purpose": _purpose,
    "external_ticket": _external_ticket,
    "approval": _approval,
    "successful_checks": _successful_checks,
    "deployment": _deployment,
    "rollback_plan": _rollback_plan,
    "exception_disclosure": _exception_disclosure,
}


def evaluate(passport: dict[str, Any], requirements: list[str]) -> list[dict[str, str]]:
    """Return one result per requirement, including gaps found in the passport."""
    results: list[dict[str, str]] = []
    for name in requirements:
        check = _CHECKS.get(name)
        if check is None:
            results.append({"id": name, "status": "gap", "detail": "未知策略项，未被检查"})
            continue
        gap = check(passport)
        results.append(
            {
                "id": name,
                "status": "gap" if gap else "pass",
                "detail": gap or CHECK_NAMES[name],
            }
        )
    return results

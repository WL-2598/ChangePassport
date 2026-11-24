"""Render a human-readable view of an existing passport (no new facts)."""

from __future__ import annotations

from typing import Any


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(_cell(item) for item in row) + " |" for row in rows)
    return lines


def render_markdown(passport: dict[str, Any], verification: dict[str, Any] | None = None) -> str:
    """Produce deterministic Markdown from a validated passport dict."""
    repository = passport["repository"]
    change = passport["change"]
    lines: list[str] = [
        "# 变更证据包 / Change Passport",
        "",
        f"- 证据包标识：`{_cell(change['id'])}`",
        f"- 仓库：`{_cell(repository['owner'])}/{_cell(repository['name'])}`",
        f"- 生成时间：`{_cell(passport['generator']['generated_at'])}`",
        "- 生成器："
        f"`{_cell(passport['generator']['name'])}` {_cell(passport['generator']['version'])}",
        f"- Schema：`{_cell(passport['schema_version'])}`",
        "",
        "## 变更与来源",
        "",
    ]
    lines.extend(
        _table(
            ["字段", "值", "来源"],
            [
                ["标题", change["title"], "GitHub" if change["title"] != "missing" else "缺失"],
                [
                    "变更目的",
                    change["purpose"],
                    "人工声明" if change["purpose"] != "missing" else "缺失",
                ],
                [
                    "外部工单",
                    (
                        f"{change['external_ticket']['reference']} "
                        f"{change['external_ticket']['url']}"
                    ).strip(),
                    "人工声明",
                ],
                ["变更链接", change["url"], change["url"]],
                ["作者", change["author"], "GitHub"],
                ["合并时间", change["merged_at"], "GitHub"],
                ["HEAD SHA", change["head_sha"], "GitHub"],
                ["Commit 数量", len(change["commit_shas"]), "GitHub"],
            ],
        )
    )
    lines.extend(["", "## 审批记录（仅 GitHub Reviews）", ""])
    if passport["approvals"]:
        lines.extend(
            _table(
                ["审批人", "时间", "原始记录"],
                [
                    [item["reviewer"], item["approved_at"], item["source_url"]]
                    for item in passport["approvals"]
                ],
            )
        )
    else:
        lines.append("未取得审批记录；不推测审批事实。")

    lines.extend(["", "## 所有 Review", ""])
    if passport["reviews"]:
        lines.extend(
            _table(
                ["Reviewer", "结论", "时间", "原始记录"],
                [
                    [item["reviewer"], item["state"], item["submitted_at"], item["source_url"]]
                    for item in passport["reviews"]
                ],
            )
        )
    else:
        lines.append("无 Review 记录。")

    lines.extend(["", "## CI / Checks", ""])
    if passport["checks"]:
        lines.extend(
            _table(
                ["名称", "结论", "完成时间", "原始记录"],
                [
                    [item["name"], item["conclusion"], item["completed_at"], item["source_url"]]
                    for item in passport["checks"]
                ],
            )
        )
    else:
        lines.append("无 Check/Status 记录。")

    lines.extend(["", "## 部署与回滚（人工声明，未独立验证）", ""])
    lines.extend(
        _table(
            ["类型", "环境", "时间", "操作者", "记录/链接"],
            [
                [
                    "部署",
                    item["environment"],
                    item["deployed_at"],
                    item["actor"],
                    item["source_url"],
                ]
                for item in passport["deployments"]
            ]
            + [
                [
                    "回滚",
                    item["environment"],
                    item["rolled_back_at"],
                    item["actor"],
                    item["source_url"],
                ]
                for item in passport["rollbacks"]
            ],
        )
    )
    lines.extend(
        [
            "",
            f"- 回滚说明/链接：`{_cell(passport['rollback_plan']['source_url'])}`",
            f"- 例外复核状态：`{_cell(passport['exception_review']['status'])}`（人工声明）",
        ]
    )
    if passport["exceptions"]:
        lines.extend(["", "### 例外", ""])
        lines.extend(
            _table(
                ["类型", "说明", "批准人", "链接"],
                [
                    [item["type"], item["description"], item["approved_by"], item["source_url"]]
                    for item in passport["exceptions"]
                ],
            )
        )

    lines.extend(["", "## 缺失与未知", ""])
    if passport["completeness"]["missing"]:
        lines.extend(
            _table(
                ["字段", "原因", "预期来源"],
                [
                    [item["field"], item["reason"], item["expected_source"]]
                    for item in passport["completeness"]["missing"]
                ],
            )
        )
    else:
        lines.append("未记录缺失字段。")
    if passport["completeness"]["unknown"]:
        lines.append("未知来源字段：" + ", ".join(passport["completeness"]["unknown"]))

    lines.extend(["", "## 数据与限制", ""])
    lines.extend(
        _table(
            ["字段", "来源", "链接"],
            [[key, value["source"], value["url"]] for key, value in passport["provenance"].items()],
        )
    )
    lines.extend(
        [
            "",
            f"内容摘要（SHA-256）：`{passport['content_digest']['value']}`",
            "内容摘要只用于检测内容变化，不是签名、防篡改证明或可信时间戳。",
            "“审批通过”不等于“变更安全”；本文件不是审计意见或合规认证。",
        ]
    )
    if verification is not None:
        gaps = verification["policy"]["gaps"]
        lines.extend(
            [
                "",
                "## 策略校验摘要",
                "",
                f"- 状态：`{_cell(verification['status'])}`",
                f"- Schema 有效：`{verification['schema']['valid']}`",
                f"- 摘要一致：`{verification['digest']['matches']}`",
                f"- 缺口数：{len(gaps)}",
            ]
        )
        for gap in gaps:
            lines.append(f"- {gap['id']}: {gap['detail']}")
    return "\n".join(lines) + "\n"

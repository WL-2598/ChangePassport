# 变更证据包 / Change Passport

- 证据包标识：`PR #42`
- 仓库：`example-org/demo-service`
- 生成时间：`2026-01-15T10:30:00Z`
- 生成器：`changepassport` 0.1.0
- Schema：`1.0.0`

## 变更与来源

| 字段 | 值 | 来源 |
| --- | --- | --- |
| 标题 | Add signed release manifest | GitHub |
| 变更目的 | Add an auditable release manifest for the checkout demo service. | 人工声明 |
| 外部工单 | OPS-1842 https://tickets.example.invalid/OPS-1842 | 人工声明 |
| 变更链接 | https://github.com/example-org/demo-service/pull/42 | https://github.com/example-org/demo-service/pull/42 |
| 作者 | dev-alice | GitHub |
| 合并时间 | 2026-01-15T09:12:00Z | GitHub |
| HEAD SHA | 2222222222222222222222222222222222222222 | GitHub |
| Commit 数量 | 2 | GitHub |

## 审批记录（仅 GitHub Reviews）

| 审批人 | 时间 | 原始记录 |
| --- | --- | --- |
| reviewer-bob | 2026-01-15T09:05:00Z | https://github.com/example-org/demo-service/pull/42#pullrequestreview-1 |

## 所有 Review

| Reviewer | 结论 | 时间 | 原始记录 |
| --- | --- | --- | --- |
| reviewer-bob | approved | 2026-01-15T09:05:00Z | https://github.com/example-org/demo-service/pull/42#pullrequestreview-1 |
| reviewer-carol | commented | 2026-01-15T09:08:00Z | https://github.com/example-org/demo-service/pull/42#pullrequestreview-2 |

## CI / Checks

| 名称 | 结论 | 完成时间 | 原始记录 |
| --- | --- | --- | --- |
| unit-tests | success | 2026-01-15T09:10:00Z | https://github.com/example-org/demo-service/actions/runs/9001 |

## 部署与回滚（人工声明，未独立验证）

| 类型 | 环境 | 时间 | 操作者 | 记录/链接 |
| --- | --- | --- | --- | --- |
| 部署 | staging | 2026-01-15T09:40:00Z | release-bot | https://github.com/example-org/demo-service/actions/runs/9001 |

- 回滚说明/链接：`https://runbooks.example.invalid/demo-service/rollback`
- 例外复核状态：`reviewed`（人工声明）

## 缺失与未知

| 字段 | 原因 | 预期来源 |
| --- | --- | --- |
| rollbacks | 人工未声明回滚记录 | declared config |

## 数据与限制

| 字段 | 来源 | 链接 |
| --- | --- | --- |
| change.title | snapshot | https://github.com/example-org/demo-service/pull/42 |
| change.purpose | declared | missing |
| change.external_ticket | declared | https://tickets.example.invalid/OPS-1842 |
| approvals | snapshot | https://github.com/example-org/demo-service/pull/42 |
| checks | snapshot | https://github.com/example-org/demo-service/pull/42 |
| deployments | declared | https://github.com/example-org/demo-service/actions/runs/9001 |
| rollback_plan | declared | https://runbooks.example.invalid/demo-service/rollback |
| exception_review | declared | missing |
| content_digest | computed | missing |

内容摘要（SHA-256）：`4b58be57a19d27870850811d1de751b461b422f312a9e1804fab924706bb90f8`
内容摘要只用于检测内容变化，不是签名、防篡改证明或可信时间戳。
“审批通过”不等于“变更安全”；本文件不是审计意见或合规认证。

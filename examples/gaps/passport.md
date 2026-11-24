# 变更证据包 / Change Passport

- 证据包标识：`PR #43`
- 仓库：`example-org/demo-service`
- 生成时间：`2026-01-15T10:30:00Z`
- 生成器：`changepassport` 0.1.0
- Schema：`1.0.0`

## 变更与来源

| 字段 | 值 | 来源 |
| --- | --- | --- |
| 标题 | Draft change without review evidence | GitHub |
| 变更目的 | missing | 缺失 |
| 外部工单 | missing | 缺失 |
| 变更链接 | https://github.com/example-org/demo-service/pull/43 | https://github.com/example-org/demo-service/pull/43 |
| 作者 | dev-alice | GitHub |
| 合并时间 | missing | 缺失 |
| HEAD SHA | 3333333333333333333333333333333333333333 | GitHub |
| Commit 数量 | 0 | GitHub |

## 审批记录（仅 GitHub Reviews）

未取得审批记录；不推测审批事实。

## 所有 Review

无 Review 记录。

## CI / Checks

无 Check/Status 记录。

## 部署与回滚（人工声明，未独立验证）

| 类型 | 环境 | 时间 | 操作者 | 记录/链接 |
| --- | --- | --- | --- | --- |

- 回滚说明/链接：`missing`
- 例外复核状态：`not_reviewed`（人工声明）

## 缺失与未知

| 字段 | 原因 | 预期来源 |
| --- | --- | --- |
| change.purpose | 配置中未填写变更目的 | declared config |
| change.external_ticket | 配置中未填写外部工单编号或链接 | declared config |
| change.merged_at | 没有可用的合并时间（commit 模式可为未知） | snapshot |
| approvals | 没有 GitHub APPROVED 审核记录 | snapshot |
| checks | 没有取到 Check/Status 记录 | snapshot |
| deployments | 人工未声明部署记录 | declared config |
| rollbacks | 人工未声明回滚记录 | declared config |
| rollback_plan | 人工未填写回滚说明或链接 | declared config |
| exception_review | 尚未人工确认例外披露 | declared config |
未知来源字段：change.purpose, change.external_ticket, approvals, checks, deployments, rollback_plan

## 数据与限制

| 字段 | 来源 | 链接 |
| --- | --- | --- |
| change.title | snapshot | https://github.com/example-org/demo-service/pull/43 |
| change.purpose | missing | missing |
| change.external_ticket | missing | missing |
| approvals | missing | https://github.com/example-org/demo-service/pull/43 |
| checks | missing | https://github.com/example-org/demo-service/pull/43 |
| deployments | missing | missing |
| rollback_plan | missing | missing |
| exception_review | declared | missing |
| content_digest | computed | missing |

内容摘要（SHA-256）：`26ba9507e0ee5517b2ba0dc44a6a083b1d858cd7edcd57a945d0262da4e3bdb9`
内容摘要只用于检测内容变化，不是签名、防篡改证明或可信时间戳。
“审批通过”不等于“变更安全”；本文件不是审计意见或合规认证。

## 策略校验摘要

- 状态：`gaps`
- Schema 有效：`True`
- 摘要一致：`True`
- 缺口数：7
- purpose: change.purpose 为 missing
- external_ticket: change.external_ticket 缺少编号或链接
- approval: 没有从 GitHub Reviews 中取到审批记录（未推测审批）
- successful_checks: 没有 Check 记录
- deployment: 没有含环境与时间的人工声明部署记录
- rollback_plan: rollback_plan.source_url 为 missing
- exception_disclosure: 尚未人工确认例外披露状态

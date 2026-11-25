# 数据模型与字段来源

Schema：`schemas/v1/passport.schema.json`（JSON Schema 2020-12）。首版字段按“能否说明来源、用途和缺失表现”筛选；没有来源的推测字段不进入模型。

| 字段 | 来源 | 用途 | 缺失时表现 |
|---|---|---|---|
| `generator` / `schema_version` | CLI 自身 | 复现与版本追踪 | 不允许缺失 |
| `repository` | 配置 | 标识仓库 | 配置校验失败 |
| `policy` | 配置 | 决定 `verify` 检查哪些策略项 | 不允许缺失；未知策略项会报缺口 |
| `change.id` / `kind` / `url` | PR 编号或 commit SHA + GitHub URL | 标识变更 | `missing` |
| `change.title` / `author` / `merged_at` / `head_sha` / `commit_shas` | GitHub PR/Commit API | 事实留痕 | `missing` 并进入 `completeness.missing` |
| `change.purpose` | 人工配置 `declared.purpose` | 说明为什么改 | `missing` 并进入缺失列表 |
| `change.external_ticket` | 人工配置 | 连接外部工单 | `missing` 并进入缺失列表 |
| `reviews` / `approvals` | GitHub Reviews API | 审批事实与原始链接 | 空数组 + 缺失条目；不推测审批 |
| `checks` | GitHub Check Runs / Statuses API | CI 结论与原始链接 | 空数组 + 缺失条目；不推测测试结果 |
| `deployments` | 人工配置 | 部署环境、时间、操作者 | 空数组 + 缺失条目；标为 `declared` |
| `rollbacks` / `rollback_plan` | 人工配置 | 回滚记录与说明链接 | 空数组 / `missing` + 缺失条目 |
| `exceptions` / `exception_review` | 人工配置 | 紧急发布与其他例外披露 | 空数组 / `not_reviewed` + 缺失条目 |
| `completeness` | 构建器计算 | 集中列出缺失和未知来源字段 | 空数组表示未记录缺失 |
| `provenance` | 构建器计算 | 逐字段记录来源（GitHub / 人工 / 快照 / 计算 / 缺失） | 每条必须有 `source` 与 `url` |
| `content_digest` | 构建器计算 | 检测内容变化 | 校验时重算，不匹配则报告 invalid |

## 重要约定

1. `missing` 表示“没有拿到或没有填写”；`unknown` 表示“来源/值不可确定”。两者都是显式字符串，不使用 `null` 代替。
2. `declared` 表示人工声明，工具**没有独立验证**。GitHub API -derived 字段保留 `source_url`，可人工点击核对。
3. `--snapshot` 生成的数据源标记为 `snapshot`，即使快照内容看起来像 GitHub API 响应；不会声称“刚刚查过 GitHub”。
4. 摘要算法：`json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`，先把 `content_digest.value` 置空，再取 UTF-8 字节的 SHA-256。同一输入与生成时间会得到相同摘要。
5. 摘要只能发现“内容变了”，不能证明谁在何时生成、不能防篡改、不具备可信时间戳属性，也不构成审计意见。

## 非目标字段

以下字段被有意排除：源代码内容、客户正文、AI 风险评分、自动生成合规结论、自动批准/拒绝发布、生产环境凭证。

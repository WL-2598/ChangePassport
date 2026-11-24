# GitHub 权限与 Action 行为

## 最小权限原则

示例工作流只声明：

```yaml
permissions:
  contents: read
  pull-requests: read
  actions: read
  checks: read
```

对应用途：

| 权限 | 用途 | 是否需要写权限 |
|---|---|---|
| `contents: read` | 读取 PR/Commit 元数据与 checkout | 否 |
| `pull-requests: read` | 读取 PR 基本信息与 Reviews | 否 |
| `checks: read` | 读取 Check Runs 结论与链接 | 否 |
| `actions: read` | 读取 workflow run 链接（部署声明的辅助核对） | 否 |

不需要 `contents: write`、`pull-requests: write`、`checks: write`、admin 权限或 `workflow` 权限。Action 不会评论 PR、不会改状态、不会创建 Release。

## Token 处理

- Action 输入 `token` 默认使用 `${{ github.token }}`；也可以传入自定义只读 token。
- CLI 只从环境变量读取（默认 `GITHUB_TOKEN`），从不接受“token 本身”作为参数。
- token 不出现在证据包、报告、Markdown 或 CLI 输出。
- 使用 `--snapshot` 时不读取 token，也不发起网络请求。

## Report-only 保证

1. `verify` 默认退出码为 0；只有显式 `--strict` 才在缺口时返回 1。
2. Action 中的验证步骤对非零退出只输出 warning，不让工作流失败。
3. 证据包作为 Artifact 保存；不自动评论、不打标签、不关闭 PR、不回滚部署。
4. 缺失信息原样展示；不自动补全、不猜测审批或部署事实。

## GitHub Enterprise

可通过 `GITHUB_API_URL` 指定 GitHub Enterprise 的 API 基址；必须是 HTTPS、无路径/查询/片段、无内嵌凭据。数据仍只发送到该 GitHub API 主机。GHES 场景尚未在客户环境实测（见 `docs/security.md`）。

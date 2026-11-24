# 15 分钟上手验证（目标用户演练用）

用途：让从未见过项目的人在 15 分钟内独立生成第一份有用的证据包。请计时并记录卡点，不要由作者代操作。当前文档描述的是**可执行的步骤**，不是“已有人完成验证”的证明。

## A. 本地离线路径（约 5 分钟，无网络 API）

1. `git clone <本仓库>`，进入目录；`python3 -m venv .venv && . .venv/bin/activate`。
2. `python -m pip install -e '.[dev]'`（首次会从 PyPI 安装依赖）。
3. `changepassport build --config tests/fixtures/config.json --snapshot tests/fixtures/snapshot.json --out dist/passport.json --generated-at 2026-01-15T10:30:00Z`。
4. `changepassport verify --input dist/passport.json`。
5. `changepassport render --input dist/passport.json --out dist/passport.md`。
6. 打开 `dist/passport.md`：能找到审批人、CI 结论、人工声明的部署、缺失字段、来源表与摘要声明。

## B. GitHub Action 路径（约 10 分钟，需要一个测试仓库）

1. 在测试仓库创建一个测试 PR（不需要真实客户仓库）。
2. 让 PR 产生一个 Review 和一次 CI Check（示例 workflow 可以只包含 `echo`，但需真正运行一次）。
3. 把 `examples/github-action/workflow.yml` 复制到测试仓库的 `.github/workflows/changepassport-demo.yml`。
4. 按 `docs/permissions.md` 设置只读 `permissions`；确认没有写权限。
5. 在测试仓库添加最小 `changepassport.json`（可用 `changepassport init` 生成后填写人工声明字段）。
6. 重新提交 PR，等待 Action 完成；下载 Artifact，检查 `passport.json`、`verify.json`、`passport.md`。
7. 删除配置里的 `purpose`（或一项人工声明），再次运行：验证报告必须出现明确的 `gap`，Action **仍然不阻断**发布。
8. 在日志与产物中搜索 token 字符串，确认没有泄漏；确认产物里没有源代码正文。

## 通过标准

- 总耗时 ≤15 分钟（含阅读文档）。
- 产物中每个字段都能回答“从哪来、怎么用、缺失会怎样”。
- 人为删除一个必需输入后，`verify` 明确报告缺口而不是崩溃或猜值。
- 全程没有向第三方服务发送代码或证据。

## 记录模板

```text
测试日期 / 参与者角色 / 环境（OS、Python 版本）：
首次生成耗时（分钟）：
卡点（命令、报错、文档歧义）：
是否看懂样例证据包：是 / 否（举例）
删除必需字段后 verify 行为：
是否有第三方上传：否 / 是（说明）
是否愿意进入付费试点讨论：是 / 否（说明决策人）
```

不得把未实际执行的步骤标记为通过。

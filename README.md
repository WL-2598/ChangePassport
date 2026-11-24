# ChangePassport

从 GitHub 的真实发布记录生成**可验证、可导出**的变更证据包，并明确标记缺失流程。不生成“合规结论”。

> 状态：工程原型可离线运行；客户访谈与付款试点**尚未开始**。没有公开 Release，也没有在任何真实客户仓库中运行过。

## 边界

- 本地 Python CLI + GitHub Action；无后端、无数据库、无默认遥测。
- 核心链路不调用大模型；不持久化客户源代码；不把证据上传到第三方。
- 查不到的数据写 `missing` / `unknown`；不推测审批、部署、测试或回滚事实。
- 内容摘要只检测内容变化，**不是**签名、防篡改证明或可信时间戳。
- 不宣称保证通过 SOC 2、ISO 27001 或任何审计。

## 15 分钟离线验证（无需 token、无需网络）

要求 Python 3.11+（目标生产版本 3.12）。

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'

# PR-0004: 最小配置
changepassport init --owner example-org --name demo-service --change 42

# PR-0003/0004: 用仓库自带的脱敏合成 Fixture 生成样例（不联网）
changepassport build \
  --config tests/fixtures/config.json \
  --snapshot tests/fixtures/snapshot.json \
  --out dist/passport.json \
  --generated-at 2026-01-15T10:30:00Z

# 校验 Schema、摘要与策略缺口（默认 report-only）
changepassport verify --input dist/passport.json --out dist/verify.json --strict

# 渲染 Markdown（不重新获取数据）
changepassport render --input dist/passport.json --verification dist/verify.json --out dist/passport.md
```

`--strict` 会在存在缺口时返回退出码 1；不加 `--strict` 时即使有缺口也只输出报告，便于 report-only 场景。删除配置里的 `purpose` 再运行 `verify`，可以看到明确的缺口而不是猜测值。

## 命令

| 命令 | 作用 |
|---|---|
| `changepassport init` | 生成最小 JSON 配置，未填事实保持 `missing` |
| `changepassport build` | 从 GitHub API 或 `--snapshot` 离线快照生成证据包 |
| `changepassport verify` | 校验 Schema、内容摘要、策略缺口 |
| `changepassport render` | 从已有 JSON 渲染 Markdown，不重新获取事实 |

## GitHub Action

见 `examples/github-action/workflow.yml`。默认 report-only、不阻断发布、以 Artifact 保存 JSON/验证报告/Markdown，权限最小化。Action 只调用 GitHub REST API；安装依赖时会访问 PyPI。详见 `docs/permissions.md` 与 `docs/security.md`。

## 缺口演示与安全

`examples/gaps/` 展示“删除必需输入后”的真实输出：7 个策略缺口、9 个记录缺失项，所有未知事实保持 `missing`，不推测审批或部署。安全边界见 `SECURITY.md` 与 `docs/security.md`。

一条命令复现全部本地检查：`bash scripts/check.sh`（格式、Lint、类型、测试、依赖审计；不联系 GitHub 或客户系统）。

## 文档索引

- 审计与边界：`docs/repo-audit.md`
- 产品章程：`docs/product-charter.md`
- 假设清单：`docs/hypotheses.md`
- 路线图与止损条件：`ROADMAP.md`
- 数据模型：`docs/data-model.md`
- 安全：`docs/security.md`
- 权限：`docs/permissions.md`
- 15 分钟上手：`docs/quickstart.md`
- 付费试点运行手册：`docs/pilot-runbook.md`
- 访谈提纲：`docs/interview-guide.md`
- 实际验证记录：`docs/validation-record.md`

## 验证记录

本地沙箱（Python 3.11.2）：`ruff format --check .`、`ruff check .`、`mypy`、`pytest`（34 项）、`pip-audit --skip-editable` 均已执行并通过。GitHub Actions 的 CI 矩阵与 [Action E2E run 45368636797](https://github.com/WL-2598/ChangePassport/actions/runs/45368636797) 均已实际跑通；完整 run ID 与失败记录见 `docs/validation-record.md`。**尚未验证**：真实客户 PR 上的人类 Review + Action、GHES、第三方渗透测试、客户访谈与付款。许可证为空白仓库新增的 Apache-2.0；未创建公开 Release。

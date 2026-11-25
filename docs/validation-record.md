# 验证记录（只记录实际执行过的事）

本文件区分“工程上跑过什么”和“商业上验证过什么”。后者目前全部未开始。

## 本地验证（沙箱，Python 3.11.2）

`bash scripts/check.sh` 实际执行并通过：

| 检查 | 结果 |
|---|---|
| `ruff format --check .` | 通过 |
| `ruff check .` | 通过 |
| `mypy`（strict，12 个源文件） | 通过 |
| `pytest` | 36 项通过 |
| `pip-audit --skip-editable` | 无已知漏洞（可编辑安装的本项目按设计跳过） |
| `python -m build --wheel` | 成功、无弃用告警；wheel 内含 `changepassport/schemas/v1/passport.schema.json`，元数据为 `License-Expression: Apache-2.0` + `License-File: LICENSE` |

## 真实 GitHub REST API 采集（匿名、只读）

对本仓库当前 commit `df911a1` 运行 `changepassport build`（**不带 `--snapshot`**），只访问 `https://api.github.com`，未使用 token：

```text
Built /tmp/cp-live-passport.json from GitHub API: 0 approvals, 4 checks, 10 recorded gaps.
change.id: df911a1707a5    commits: 1    checks: 4
```

4 条 Check 来自该 commit 上真实存在的 CI run；没有 Review、部署和人工声明，因此保留 10 个缺口，`verify --strict` 按预期退出 1。

**这次运行发现并修复了一个真实 bug**：`/check-runs` 返回的是 `{total_count, check_runs: [...]}` 包装对象，而收集器原按数组解析，导致首次 live build 失败。现已在 `collectors/github.py` 中解包，并新增两个单元测试：包装响应解包、API 错误降级为缺口而非中断。修复后重新 live build 成功。这证明“只用合成 Fixture 测试”不足以覆盖真实 API 形态。

仍未验证：带人类 Review 的真实 PR 采集、GHES、带 token 的私有仓库。

## GitHub Actions（真实 runner）

| 用途 | Run ID | 结果 |
|---|---|---|
| CI 主矩阵（3.11 / 3.12），首次实现 | [45348090402](https://github.com/WL-2598/ChangePassport/actions/runs/45348090402) | 成功 |
| 文档更新后的 CI 复验 | [45348198201](https://github.com/WL-2598/ChangePassport/actions/runs/45348198201) | 成功 |
| 配置校验/缺口示例后的 CI | [45368249936](https://github.com/WL-2598/ChangePassport/actions/runs/45368249936)、[45368195276](https://github.com/WL-2598/ChangePassport/actions/runs/45368195276) | 成功 |
| 临时 E2E 工作流首次运行 | [45368314964](https://github.com/WL-2598/ChangePassport/actions/runs/45368314964) | 成功；Action 生成并上传了三份产物，检查步骤断言通过 |
| 验证脚本一次失败（临时变量名写错） | [45368482260](https://github.com/WL-2598/ChangePassport/actions/runs/45368482260) | 失败；已修正脚本后重跑，不掩盖失败记录 |
| Action E2E 最终复验 | [45368636797](https://github.com/WL-2598/ChangePassport/actions/runs/45368636797) | 成功 |
| 最终 CI 复验 | [45368636747](https://github.com/WL-2598/ChangePassport/actions/runs/45368636747) | 成功 |
| Action 版本升级后的 CI 复验 | [45424560848](https://github.com/WL-2598/ChangePassport/actions/runs/45424560848) | 成功；Node 20 弃用告警消失 |
| Action 版本升级后的 E2E 复验 | [45424560788](https://github.com/WL-2598/ChangePassport/actions/runs/45424560788) | 成功；annotation 仅有我方结果，无官方 action 告警 |

最新 E2E 的 GitHub annotation 原文：`status=pass schema=True digest=True gaps=0 source=snapshot`。

E2E 覆盖的是：checkout → 本地 composite Action → 安装 CLI → 用脱敏快照 `build` → `verify` → `render` → 上传 Artifact → 在 runner 上断言 JSON/Markdown 内容。快照模式证明**收集阶段没有网络请求**；产物来源被标为 `snapshot`，不冒充实时 GitHub API。

## 明确限制

- Artifact 已由 GitHub 保存，但当前沙箱无法下载 `actions.githubusercontent.com` 的 blob（网络白名单限制），因此沙箱内没有对下载后的文件再次逐字节校验；runner 内断言已通过。
- 尚未在真实 PR 上产生人类 Review 并跑 Action；审批缺口只在合成 Fixture 与单元测试中验证。
- 未测试 GitHub Enterprise Server（GHES）环境。
- 未做第三方渗透测试或客户安全问卷。
- 未进行任何客户访谈、Pilot 收款、续费或真实发布复用。

## 商业验证状态

| 门槛 | 状态 |
|---|---|
| 第 14 天问题门（≥8 展示真实材料、≥5 讨论试点） | **未开始** |
| 第 45 天付款门（3 个已收款试点） | **未开始** |
| 第 90 天持续付费门（≥2 转持续付费） | **未开始** |

工程验证不能替代上述任何一项。

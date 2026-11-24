# 缺口示例：缺失事实不被推测

这个目录展示“必需输入被删除后”的真实输出，用于访谈和试点演示：

- `passport.json`：由 `tests/fixtures/config_missing.json` + `tests/fixtures/snapshot_missing.json` 离线生成（合成数据）。
- `verify.json`：`changepassport verify` 的报告，状态为 `gaps`，7 个策略缺口。
- `passport.md`：包含验证摘要的阅读版，明确列出缺失字段与来源。

复现命令：

```bash
changepassport build --config tests/fixtures/config_missing.json \
  --snapshot tests/fixtures/snapshot_missing.json --out /tmp/gaps.json \
  --generated-at 2026-01-15T10:30:00Z
changepassport verify --input /tmp/gaps.json --out /tmp/verify.json
changepassport render --input /tmp/gaps.json --verification /tmp/verify.json --out /tmp/gaps.md
```

预期现象：

1. `change.purpose`、外部工单、审批、CI、部署、回滚计划写为 `missing` 或空数组，不会被模型或规则补全。
2. `completeness.missing` 逐项列出 9 个缺失来源；`verify.json` 给出 7 个策略缺口。
3. 默认 `verify` 返回退出码 0（report-only）；加 `--strict` 才返回 1。
4. 内容摘要依然一致：缺口本身是事实，不影响摘要校验。
5. 这些文件不含任何真实客户数据、代码或 token。

注意：这是**合成演示**，不是客户访谈证据；不要把本文中的“缺口”描述成某真实团队的问题。

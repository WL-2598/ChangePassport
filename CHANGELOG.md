# Changelog

本项目遵循“先可验证、再扩展”的原则。未实际运行的验证不会记录为通过。

## Unreleased

### Added

- `docs/compliance-references.md`：用公开资料解释字段设计动机，并明确“不是认证结论”。
- `docs/validation-record.md`：本地检查、GitHub CI 与 Action E2E 的真实 run ID（含一次失败后修正的记录），以及明确的未验证项。
- `examples/github-action/e2e-validation.yml`：可手动重跑的 Action E2E 工作流副本。
- `examples/gaps/`：删除必需输入后的 JSON/验证报告/Markdown 缺口示例，含 Golden Test。
- `scripts/check.sh`：一条命令复现全部本地质量门禁。
- 根目录 `SECURITY.md`，指向完整安全与权限文档。

### Fixed

- 真实 GitHub API 采集发现 `/check-runs` 返回包装对象而非数组；收集器现正确解包，API 错误改为记录缺口而非中断整个 build（新增 2 个单元测试）。
- 仓库审计报告与项目章程、假设清单、访谈提纲、验证阶段路线图。
- Python 工程骨架、测试与 CI（格式、类型、测试、依赖安全检查）。
- `schemas/v1/passport.schema.json`、手工样例与脱敏 Fixture。
- 本地 CLI `init` / `build` / `verify` / `render`，GitHub 收集器与 report-only Action。
- 安全、权限、数据模型、试点运行手册文档。

### Changed

- 空白仓库仅有的 `README.md` 扩充为可复制的本地验证入口。
- 配置校验改为严格模式：未知键、错误类型和缺失的声明字段会给出明确错误；Markdown 中缺失事实的来源列显示“缺失”。
- 按 PEP 639 更新许可证元数据（SPDX 字符串 + `license-files`，构建后端最低 77.0.3），移除构建告警。
- GitHub Actions 升级到 `checkout@v7.0.1`、`setup-python@v7.1.0`、`upload-artifact@v7.0.2`，消除 Node 20 弃用告警。

### Security / business boundaries

- 未创建公开 Release，未修改既有许可证，未购买云服务，未联系客户或对外宣传。
- 未收集任何客户数据、真实访谈、订单或收入。

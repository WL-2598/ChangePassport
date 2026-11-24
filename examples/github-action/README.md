# GitHub Action 示例

`workflow.yml` 是 report-only 的最小示例：只读权限、只访问 GitHub API、产物作为 Artifact 保存，缺失字段会显示出来，**不会阻断 PR**。

在本仓库试用时，把 `workflow.yml` 复制到 `.github/workflows/changepassport-demo.yml`，然后创建一个测试 PR。在别的仓库使用时，把 `uses: ./` 换成你选择的提交引用，并确认已按 `docs/permissions.md` 设置权限。

`changepassport.json` 示例模板见仓库根目录执行 `changepassport init` 的输出；所有人工声明字段默认是 `missing`，必须由使用者填写，工具不会推测。

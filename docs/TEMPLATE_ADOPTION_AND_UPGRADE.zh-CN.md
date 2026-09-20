# PPF Reference Template 的采用与升级

`templates/quarto-book/` 是 PPF 的可执行 reference implementation。其机器可读升级边界由 `template-manifest.yaml` 定义。

## 三类路径

- **upstream-managed**：通用工具链 wrapper、校验 helper 等，可以按固定 PPF revision 更新；
- **merge-managed**：`publishing.yaml`、`cloudflare-builds.yaml`、`Makefile`、Wrangler/CI 配置等，需要比较旧模板、项目当前状态和新模板；
- **project-owned**：正文、参考文献、assets、项目专用 validator 与人类 publication decisions，不得由 PPF 升级自动覆盖。

## 升级纪律

PPF 升级不得：

- 把 build success 当作 publication authorization；
- 覆盖 provider actual state；
- 重置 canonical identity；
- 把已退休的 provider 自动重新启用；
- 把 token、secret、password 或 private key 写进 Git；
- 因模板更新覆盖项目自己的 source content。

Starter 或 AI Agent 应以 adopted commit 为 base 做三方比较，并通过 PR 与现有项目 gate 完成升级。

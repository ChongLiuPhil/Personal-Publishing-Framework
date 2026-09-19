# PPF v0.1 Reference Implementation Audit

**日期：** 2026-09-19  
**分支：** `reference-implementation-v0.1`  
**状态：** PASS — initial static audit + downstream runtime validation + current root-level template CI

> 本文件记录最初 reference implementation 分支的静态审计。此后真实 downstream pilot 已完成，并对当前 `main` 模板产生改进；见 `FIRST_PILOT_LESSONS.zh-CN.md`。

## 审计对象

`templates/quarto-book/`

该目录是 PPF 的第一套 reference implementation，不是 PPF 规范本身。

## 1. Profile 模型

已确认：

- `_quarto.yml` 默认 profile = `web`；
- Web 输出目录 = `_book`；
- EPUB 输出 = `_publication/epub`；
- PDF 输出 = `_publication/pdf`；
- DOCX 输出 = `_publication/docx`；
- LaTeX 输出 = `_publication/latex`。

PASS。

## 2. Continuous vs on-demand

`publishing.yaml`：

- Web = `continuous`；
- EPUB/PDF/DOCX/LaTeX = `on-demand`。

`web.yml`：
- PR / push 运行统一 `make web-publish-check`；
- GitHub Actions 只负责独立 Web validation；
- 不持有 Cloudflare deployment credential；
- 不执行 Cloudflare production deploy。

`cloudflare-contract-ci.yml`：
- 固定 Node / Wrangler；
- 从空白 runner 安装并校验固定 Quarto；
- 运行 `make cloudflare-build`；
- 模拟 Workers Builds 环境，但不部署。

`build-publication.yml`：
- 仅 `workflow_dispatch`；
- 明确选择 EPUB/PDF/DOCX/LaTeX；
- 上传 GitHub Actions artifact；
- 不自动 release / publish。

PASS。

## 3. Cloudflare 配置一致性

`wrangler.jsonc`：

`assets.directory = ./_book`

与 Quarto Web profile 和 workflow 验证路径一致。

PASS。

## 4. Publication intent vs provider implementation

- `publishing.yaml`：声明 publication intent；
- `wrangler.jsonc`：Cloudflare provider-specific implementation。

二者保持分离。

PASS。

## 5. Source / artifact 边界

canonical source 示例：
- QMD；
- BibTeX；
- metadata；
- original assets。

派生目录：
- `_book/`
- `_publication/`

派生目录进入 `.gitignore`，不替代 canonical source。

PASS。

## 6. Workflow execution status

历史上，本模板只有静态审计，因为 workflow 位于 `templates/quarto-book/.github/workflows/`。

随后：

1. downstream pilot `epistemology-textbook` 完成真实 runtime validation；
2. PPF 新增根级 `.github/workflows/reference-template-ci.yml`；
3. root-level CI 会进入 `templates/quarto-book/`，安装固定 Wrangler，并执行：
   - `make check`
   - `make cloudflare-build`
4. 因此当前 reference template 不再只依赖静态审计，而是拥有持续 upstream execution validation。

## 结论

**PASS。**

PPF v0.1 Quarto reference implementation 可以合并，并进入真实项目 pilot 阶段。


## 7. 后续 Runtime Pilot

最初审计提出的 downstream runtime validation 已由 `ChongLiuPhil/epistemology-textbook` 完成。

真实运行验证了：

- Web profile：PASS；
- rendered HTML integrity：PASS；
- EPUB / PDF / DOCX / LaTeX：全部 PASS；
- production-path GitHub Pages deployment：PASS。

Pilot 同时促成当前模板的后续修订：

- continuous Web validation 与 provider deployment activation 分离；
- repository-owned `make web-publish-check` 成为统一 gate；
- Workers Builds + GitHub App 成为默认 Cloudflare Git integration reference；
- `cloudflare-builds.yaml` 成为 PPF machine contract；
- Node / Wrangler / Quarto 工具链固定并由 contract CI 执行验证；
- one-format-per-request artifact verification；
- provider provisioning 与 recurring deploy credential 分离；
- Cloudflare MCP/OAuth 作为可选 AI account automation，而不是 PPF 必需条件。

详细记录见：

`docs/FIRST_PILOT_LESSONS.zh-CN.md`

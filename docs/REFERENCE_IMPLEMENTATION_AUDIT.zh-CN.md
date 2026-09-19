# PPF v0.1 Reference Implementation Audit

**日期：** 2026-09-19  
**分支：** `reference-implementation-v0.1`  
**状态：** PASS — static reference-template audit

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
- PR / push 构建 Web；
- 检查 `_book/index.html`；
- 只有 main push 才执行 Cloudflare deploy。

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

PPF 仓库自身没有该模板的 GitHub Actions run。

原因：workflow 位于 `templates/quarto-book/.github/workflows/`，它是**下游项目模板**，不是 PPF 根目录 workflow。

因此本审计结论是 **static template validation**，不是声称模板已经在 PPF 仓库内执行通过。

实际执行验证应在第一个 downstream pilot（`epistemology-textbook`）中完成。

## 结论

**PASS。**

PPF v0.1 Quarto reference implementation 可以合并，并进入真实项目 pilot 阶段。

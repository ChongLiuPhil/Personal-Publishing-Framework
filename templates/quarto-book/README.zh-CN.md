# PPF Quarto Book 参考模板

本目录是 **Personal Publishing Framework（PPF）** 的第一套可执行 reference implementation。

它演示一套具体技术栈：

```text
QMD / Markdown / BibTeX
        |
      Quarto
        |
   +----+------------------+
   |                       |
   v                       v
HTML / Web            按需格式
   |                   EPUB / PDF
GitHub Actions         DOCX / LaTeX
   |
Cloudflare Workers
Static Assets
```

这些技术只是参考实现，不是 PPF 的规范性要求。PPF 本身不强制使用 GitHub、Quarto 或 Cloudflare。

## 默认行为

`_quarto.yml` 把 `web` 声明为默认 profile。

因此：

```bash
quarto render
```

只渲染 Web Edition。

只有明确要求其他出版格式时才使用：

```bash
quarto render --profile epub
quarto render --profile pdf
quarto render --profile docx
quarto render --profile latex
```

## 持续 Web 发布

`.github/workflows/web.yml`：

- pull request 和 `main` push 都会构建 Web profile；
- 检查 `_book/index.html` 是否存在；
- pull request 和 `main` push 始终可以构建并验证 Web profile；
- provider deployment 默认保持 staged；
- 只有 `WEB_DEPLOY_ENABLED=true` 且配置了 `PRODUCTION_URL` 时，验证通过的 `main` push 才部署到 Cloudflare；
- deployment 后执行 production verification。

启用生产部署前，需要先确认 Worker / deployment target 已准备好，然后在 GitHub repository secrets 中配置：

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

repository variables：

- `PRODUCTION_URL`
- `WEB_DEPLOY_ENABLED=true`

在 `PRODUCTION_URL` 尚未配置时把 `WEB_DEPLOY_ENABLED` 设为 `true` 会让 workflow 主动失败，而不是静默进入半配置状态。

Cloudflare API token 应尽量采用最小权限范围。对于已经存在的 Worker，长期 CI credential 应优先只授予该 Worker 的部署/编辑权限；创建 Worker 或修改 Custom Domain/Route 等一次性 provisioning 权限不应无期限保留在日常内容发布 credential 中。

## 按需格式

`.github/workflows/build-publication.yml` 只通过 `workflow_dispatch` 手工启动。

用户明确选择 EPUB、PDF、DOCX 或 LaTeX 中的一种格式。workflow 会验证对应输出扩展名确实存在，再把生成文件上传为 GitHub Actions artifact。

PDF 等格式可能需要项目专用字体、TeX packages 或其他依赖；这些应由具体项目在 workflow 中增加，而不是强迫所有 PPF 项目共同安装。

**Build 不等于 Release，也不等于外部 Publish。**

## 使用前需要修改

在真实项目采用本模板前：

1. 修改 `_quarto.yml` 中的书名和作者；
2. 修改 `publishing.yaml` 中的 project id、title 和 deployment 信息；
3. 修改 `wrangler.jsonc` 中的 Worker 名称；
4. 先完成 provider staging / readiness，再填写 canonical production URL；
5. 只有 deployment target、secrets 与生产 URL 都准备好后，才设置 `WEB_DEPLOY_ENABLED=true`；
6. 替换示例 QMD；
7. 添加 bibliography 和原始 assets；
8. 根据真实项目需要，在 deploy 前增加更严格的 source/output validation。

## 输出目录

```text
_book/
  持续发布的 HTML

_publication/
  epub/
  pdf/
  docx/
  latex/
```

这些目录都是派生成果，因此默认不进入 Git 历史。

## Publication contract 与实现配置分离

`publishing.yaml` 声明的是**发布意图**。

`wrangler.jsonc` 声明的是 Web delivery 的一种 **Cloudflare 实现**。

把二者分开，未来即使替换 Cloudflare，也不需要重新定义 PPF 的出版模型。

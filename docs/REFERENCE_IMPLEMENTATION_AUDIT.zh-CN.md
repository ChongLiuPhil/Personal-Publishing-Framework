# PPF v0.1 Reference Implementation Audit

**日期：** 2026-09-19  
**分支：** `reference-implementation-v0.1`  
**状态：** PASS — initial static audit + downstream runtime validation + verified Cloudflare staging/runtime evidence + current root-level template CI

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

该句是最初审计阶段的历史结论。真实 downstream pilot 随后已经完成；当前 reference implementation 不再处于“等待 pilot”状态。


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


## 8. Upstream Continuous Template CI

PPF root-level `Reference Template CI` 已实际执行通过。

- 首次持续验证记录：run `35428973528`；
- 当前 main 参考实现验证：run `35444948817` @ `3e884e58db113a3ef5d499a6726784ea27fdd48f`，PASS；
- exact Wrangler install/version check：PASS
- publication contract validation：PASS
- clean-runner pinned Quarto install + SHA-256 verification：PASS
- `make cloudflare-build`：PASS
- rendered Web artifact validation：PASS

因此当前 reference implementation 同时拥有：

1. initial static audit；
2. downstream real-project runtime evidence；
3. upstream continuous template execution validation。


## 9. 当前 Cloudflare staging/runtime evidence

后续真实 downstream pilot 已把 reference implementation 从“repository contract 可执行”推进到真实 provider staging/runtime 验证。

`ChongLiuPhil/epistemology-textbook` 当前持久证据记录：

- Cloudflare account connection：VERIFIED；
- Cloudflare GitHub App / repository connection：VERIFIED；
- Worker target：VERIFIED；
- main Workers Build：PASS；
- non-production preview：PASS；
- main workers.dev HTTP/content runtime：PASS；
- preview workers.dev HTTP/content runtime：PASS；
- post-merge main push 再次触发 Workers Build：PASS。

这些证据支持 reference implementation 中：

- repository intent 与 provider actual state 分离；
- build success 与 runtime success 分离；
- preview/runtime verification 作为 cutover 前 gate；
- provider action 后 write-back；
- provider production branch 与 canonical production 分离。

但它们**不**证明 Cloudflare 已成为 canonical production。

当前 publication state 仍是：

```text
GitHub Pages = current canonical production
Cloudflare workers.dev = verified staging/runtime target
Custom Domain = not cut over
canonical URL migration = not done
legacy Pages policy = unresolved
```

## 10. Security-profile evidence boundary

Cloudflare reference security profiles 的证据边界必须按真实 pilot 解释：

- **Profile A — Workers Builds Native**：operationally verified；managed user token scope 比纯 static Worker routine deploy 所需更宽，不能称为 per-Worker least privilege；
- **Profile B — Hardened External CI**：**candidate / validate-only PASS**；candidate workflow 的 repository/build validation 已通过，但 credential、preview、production deployment steps 未执行，**不是 production-tested**；
- **Profile C — Future Native Granular**：当前 provider product capability 不支持所需组合，因此记录为 unavailable。

Production security profile 的最终选择仍属于 human-governed security decision。

## 11. 当前审计结论

当前 reference implementation 已拥有四层真实 evidence：

1. initial static audit；
2. downstream source/build/multi-format runtime validation；
3. downstream Cloudflare account/build/preview/workers.dev runtime validation；
4. upstream continuous Reference Template CI。

仍未验证、不得提前声称完成的项目包括：

- Cloudflare Custom Domain cutover；
- canonical URL migration；
- legacy GitHub Pages policy execution；
- Profile B production deployment；
- Profile C native granular credential support；
- Amazon KDP / Kindle 与 external publisher delivery。

因此 reference implementation 当前可以被描述为 **real-pilot-backed staging/runtime reference**，但不能被描述为已经完成 Cloudflare canonical production cutover。

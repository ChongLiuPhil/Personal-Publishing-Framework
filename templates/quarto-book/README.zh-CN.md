# PPF Quarto Book 参考模板

本目录是 **Personal Publishing Framework（PPF）** 的可执行 Quarto reference implementation。

它演示：

```text
QMD / Markdown / BibTeX
        |
        +--> GitHub Actions
        |      validation -> make web-publish-check
        |
        +--> Cloudflare Workers Builds
        |      连接 private GitHub repository
        |      main push -> build -> deploy
        |      默认 Worker-scoped Access
        |      restricted by default
        |
        +--> 明确请求
               EPUB / PDF / DOCX / LaTeX
```

这些技术只是 reference implementation，不是 PPF 的规范性要求。

## 唯一 Web publication gate

仓库把 Web 构建和质量验证集中在：

`make web-publish-check`

它执行：

1. publication contract validation；
2. Quarto Web render；
3. rendered Web artifact validation。

GitHub Actions 与 Cloudflare Workers Builds 都调用这一 gate，避免维护两套容易漂移的验证逻辑。

## GitHub Actions 的职责

`.github/workflows/web.yml` 负责独立 validation：

- checkout；
- Python；
- Quarto；
- `make web-publish-check`。

`.github/workflows/deploy-cloudflare.yml` 继续保留给可选的高级 External-CI Profile，但不再是默认 production 路径。默认路径是在每个项目完成一次 repository connection 后使用 Cloudflare Workers Builds。

`.github/workflows/cloudflare-contract-ci.yml` 从干净 runner 验证锁定的 Cloudflare/Wrangler build contract，但不会部署。

## Cloudflare integration 机器契约

`cloudflare-builds.yaml` 记录 PPF reference implementation 期望的 account-side 配置：

- Git repository；
- production branch；
- non-production branch builds；
- root directory；
- build command；
- deploy command；
- preview deploy command；
- Worker name；
- 工具链版本；
- connection/readiness 状态；
- security policy。

**Cloudflare 不会自动读取这个 YAML。**

它是 PPF machine contract，供 Agent 与 CI 使用。Reference 默认描述 Workers Builds Git integration、每项目一次连接、Worker-scoped Access 与 Preview 安全；可选 `external_ci` 区块保留 GitHub Actions + Trusted Secret Broker 高级 Profile。

## Source visibility / publication visibility / access / canonical identity

Reference template 现在显式展示四层独立状态：

~~~yaml
source:
  visibility: private

publication:
  web:
    authorization_state: not-authorized
    visibility: restricted
    access:
      mode: authenticated
      implementation: cloudflare-access
      policy_ref: shared-reader-access

deployment:
  web:
    provider_url: null
    canonical_identity:
      type: null
      url: null
~~~

这些是新配置原创或未发布作品的安全参考默认：private source、restricted Web、authenticated access，并且尚未获得 production publication authorization。项目以后可以显式选择并记录其他组合。

合法 downstream 组合包括：

~~~text
private source + public Web
private source + restricted Web
public source + restricted Web
restricted Web + authenticated access
~~~

不要因为 repository 是 private 就把 Web 自动设成 private，也不要因为 Worker endpoint 已经可访问就把它自动设成 canonical。

当 Web publication 需要 restricted/private access 时，Cloudflare reference 可以使用 Cloudflare Access；具体 mapping 见：

`docs/CLOUDFLARE_ACCESS_PROFILE.zh-CN.md`

该文件是 dated provider reference，不是 PPF conformance requirement。

## 推荐项目接入

普通新项目的首选路线是：

```text
private GitHub repository
-> 每项目一次 Cloudflare Git 授权
-> Workers Builds
-> Worker-scoped Access
-> 验证第一次 restricted deployment
-> 再 push 一次
-> 确认无需重新授权即可自动部署
```

这条路线明确允许每个项目一次短人工 bootstrap；账户级全自动属于可选优化，不再是前置条件。

详见：

- `docs/PER_PROJECT_GITHUB_CLOUDFLARE_SETUP.zh-CN.md`
- `docs/CLOUDFLARE_GITHUB_AUTHORIZATION.zh-CN.md`

真实 UI 字段属于 dated implementation observation。如果 Provider UI 变化，不得猜；应重新读取当前官方文档，并通过实际 build/runtime state 验证。

## Cloudflare security profiles

Workers Builds 原生 Git integration 与真正 per-Worker least-privilege deployment credential 仍是不同路径。

PPF reference 提供：

- **Profile A — Workers Builds Native**：**默认每项目引导式配置**，已有真实 pilot；Provider 管理的 build credential 权限范围较理想最小权限更宽；
- **Profile B — Agent-Provisioned External CI**：高级可选 Profile；GitHub Actions + Trusted Secret Broker 安装的 account-owned individual-Worker `Editor` token；
- **Profile C — Future Native Granular**：如果未来 Workers Builds 支持所需 account-owned per-Worker credential，则可采用的未来原生组合。

Installable template 默认选择 Profile A。Profile B 继续保留实现，但在 live Provider acceptance 完成前不得写成 production-accepted。

## Runtime verification reference

Build success 不等于 runtime success。Provider integration 完成后，可以使用只读 helper：

~~~bash
python scripts/verify_public_site.py https://example.invalid \
  --path / \
  --path /representative-page.html \
  --expect "Expected visible text"
~~~

该 helper 验证 HTTP 200、UTF-8 页面、代表性 paths、可选内容 marker 和有限数量的本地 assets。

它**不**替代：

- provider build metadata 中的 expected Git/source revision 核对；
- 项目专用 navigation/content assertions；
- migration 期间对 incumbent production health 的验证；
- explicit canonical production cutover。

这些 gate 应由 downstream 项目根据实际结构补充。

## Workers Builds Native 是新项目默认

Installable template 现在为普通新项目默认使用 Workers Builds 原生 Git integration。使用者可以完成一次短的项目连接与 Access 配置；之后普通 push 应自动部署。

需要更强 credential isolation 时，仍可显式选择高级 External-CI Profile。

任何 credential：

- 不得进入 Git；
- 不得写进聊天或 README；
- 应使用所选 Profile 当前能够支持的最小权限。

## 固定工具链

本模板固定：

- Node 24：`.nvmrc`
- Wrangler 4.135.0：`package.json`
- Quarto 1.10.18：`scripts/ensure_quarto.sh`

Cloudflare build wrapper 不假设 provider 预装 Quarto。它下载固定 release，并在使用前验证 SHA-256。

## 按需格式

`.github/workflows/build-publication.yml` 只通过 `workflow_dispatch` 启动。

用户一次明确选择 EPUB、PDF、DOCX 或 LaTeX 中一种格式；workflow 验证对应 artifact 存在后上传 GitHub Actions artifact。

重型格式需要的字体、TeX packages 或其他项目专用依赖，应由 downstream 项目按需增加。

**Build 不等于 Release，也不等于外部 Publish。**

## 采用模板前必须修改

1. 替换 `_quarto.yml` 中的书名和作者；
2. 替换 `publishing.yaml` 中的 project id / title；
3. 替换 `cloudflare-builds.yaml` 中的 `OWNER/REPOSITORY` 与 Worker name；
4. 替换 `wrangler.jsonc` 中的 Worker name；
5. 根据项目增加 source/output validation；
6. 替换示例 QMD、bibliography 与 assets；
7. 运行 GitHub reference contract CI；
8. 把 private repository 连接到 Cloudflare Workers Builds，并在提示时授权当前 repository；
9. 给 Worker 启用 Worker-scoped Access，或验证已有 account-wide Access 确实覆盖它；
10. 完成第一次 restricted deployment，并在启用 Preview 前验证匿名拒绝；
11. 再做一次无害 push，确认 Workers Builds 无需重新授权即可自动部署；
12. 确认 private-source / restricted-Web 安全默认，或明确授权并记录有意偏离；
13. 区分 provider URL 与 canonical identity；
14. 最后才决定 Custom Domain、canonical URL 与 public cutover。

## 输出目录

```text
_book/
  continuous Web artifact

_publication/
  epub/
  pdf/
  docx/
  latex/
```

这些都是派生输出，默认不进入 Git 历史。

## Publication contract 与 provider implementation 分离

基础设施身份验证使用 Cloudflare Access。出版访问不得另加项目级共享密码或会话门；只有真正提供应用级用户账户的项目才自行实现应用身份验证。账户级、Worker 级与预览保护方式见 PPF `docs/CLOUDFLARE_ACCESS_PROFILE.zh-CN.md`。

- `publishing.yaml`：发布意图；
- `cloudflare-builds.yaml`：PPF 的 provider integration machine contract；
- `wrangler.jsonc`：Cloudflare Wrangler 原生实现配置；
- Cloudflare account settings：真实 provider-side state。

四者不应被混成同一真值源。

更高层的 provider-integration 架构研究见：

`../../docs/PROVIDER_INTEGRATION_PATTERN_RESEARCH.zh-CN.md`

该文件当前是 `AI-PROPOSED / NON-NORMATIVE`，不会改变本模板的现行 contract。

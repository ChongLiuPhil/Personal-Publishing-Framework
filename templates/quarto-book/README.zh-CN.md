# PPF Quarto Book 参考模板

本目录是 **Personal Publishing Framework（PPF）** 的可执行 Quarto reference implementation。

它演示：

```text
QMD / Markdown / BibTeX
        |
        +--> GitHub Actions
        |      validation -> make web-publish-check
        |      deployment -> durable publication authorization gate
        |                 -> project-scoped Worker Editor credential
        |                 -> wrangler deploy
        |
        +--> Cloudflare Worker
        |      account-wide Access baseline
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

`.github/workflows/deploy-cloudflare.yml` 是首选 External-CI Profile 的 production deployment workflow。它读取持久化 `publishing.yaml`，只有 Web deployment 同时处于 authorized + enabled 时才构建并使用 repository-scoped Cloudflare secrets 执行 `wrangler deploy`；否则保持 no-op。

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

它是 PPF machine contract，供 Agent / Provisioner 与 CI 使用。首选 External-CI Profile 中，它描述 GitHub Actions deployment、Secret Broker 边界、Worker creation authority 与 Access 前置条件；Native Profile 中仍可描述 Workers Builds 配置。

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

## 推荐平台接入

未来 Agent 自动配置的新项目，首选路线是：

```text
一次 GitHub provisioning authorization
+ 一次 Cloudflare provisioning authorization
        |
        v
Project Provisioner
-> private repository
-> protected Worker
-> secret broker
-> GitHub Actions deploy
```

已批准平台范围内的新 repository 不应再次要求 Cloudflare GitHub App 授权。

详见：

- `docs/AGENT_PROVISIONED_EXTERNAL_CI.zh-CN.md`
- `docs/CLOUDFLARE_GITHUB_AUTHORIZATION.zh-CN.md`

真实 UI 字段只是 dated implementation observation。2026-09-19 pilot 的 Observed UI Mapping 见：

`docs/CLOUDFLARE_OBSERVED_UI_MAPPING.zh-CN.md`

如果 provider UI 与该映射不同，不得猜；应重新读取当前 UI、official docs 与 downstream machine contract，并通过实际 build/runtime state 反向验证。

当执行环境具备 Cloudflare MCP/API 与 GitHub App/API 能力时，人类通常只需完成两项平台级授权。随后 Agent 在已批准范围内配置后续项目。Public release、新 reader scope、新 domain/DNS authority 与 permission expansion 继续保持独立 human gate。

## Cloudflare security profiles

Workers Builds 的原生 Git integration 与真正 per-Worker least privilege 在当前 Cloudflare 产品上不是完全同一个路径。

PPF reference 提供：

- **Profile A — Workers Builds Native**：已有真实 pilot 证据的 provider-native Profile，但 build-token scope 较宽；
- **Profile B — Agent-Provisioned External CI**：未来新项目自动配置的首选 Profile；GitHub Actions + trusted secret broker 安装的 account-owned individual-Worker `Editor` token；
- **Profile C — Future Native Granular**：等待 Workers Builds 支持 account-owned per-Worker token 的未来原生组合。

详见：

`docs/CLOUDFLARE_SECURITY_PROFILES.zh-CN.md`

模板现在为 Agent 自动配置的新项目选择 Profile B。Repository implementation 与 CI validation 已存在，但还没有记录一次从空白项目开始的 Profile B production acceptance；在该 pilot 通过前不得写成 production-tested。

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

## External CI 是新项目 Provisioning 默认

可安装模板现在为 Agent 自动配置的新项目采用：

`GitHub Actions + Wrangler + account-owned individual-Worker Editor token`

Workers Builds Native 继续作为明确选择的 provider-native Profile，也是当前已有真实 pilot 证据的路径。

任何 token：

- 不得进入 Git；
- 不得写进聊天或 README；
- 应采用满足任务所需的最小权限；
- 一次性 provisioning 权限应与长期 deployment 权限分离。

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
8. 验证平台 GitHub / Cloudflare provisioning principal 与 account-wide Access baseline；
9. 由 trusted secret broker 安装项目专属 Worker deployment credential，token 值不得进入模型；
10. 先部署 restricted workers.dev 并验证匿名拒绝，再决定是否启用 Preview；
11. 确认 private-source / restricted-Web 安全默认，或明确授权并记录有意偏离；
12. 区分 provider URL 与 canonical identity；
13. 最后才决定 Custom Domain、canonical URL 与 public cutover。

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

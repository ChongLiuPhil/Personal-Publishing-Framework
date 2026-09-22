# PPF Quarto Book 参考模板

本目录是 **Personal Publishing Framework（PPF）** 的可执行 Quarto reference implementation。

它演示：

```text
QMD / Markdown / BibTeX
        |
        +--> GitHub Actions
        |      make web-publish-check
        |      (独立质量验证)
        |
        +--> Cloudflare Workers Builds
        |      bash scripts/cloudflare_build.sh
        |        -> pinned Quarto
        |        -> make web-publish-check
        |      preview -> wrangler versions upload
        |      main    -> wrangler deploy
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

`.github/workflows/web.yml` 只做独立 validation：

- checkout；
- Python；
- Quarto；
- `make web-publish-check`。

它**不**持有 Cloudflare token，也不负责 Cloudflare production deployment。

`.github/workflows/cloudflare-contract-ci.yml` 进一步模拟 Workers Builds 环境：

- Node 24；
- Wrangler 4.135.0；
- Python；
- checksum-verified Quarto 1.10.18；
- `make cloudflare-build`。

这个 workflow 仍然**不会部署**；它证明模板从空白 runner 能够构建。

## Workers Builds 机器契约

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

它是 PPF 的 machine contract，供 AI Agent 或人类操作者把参数配置到 Cloudflare Workers Builds。

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

## 推荐账户接入

默认参考路线：

```text
AI Agent
   |
   +--> Cloudflare OAuth / MCP

Cloudflare
   |
   +--> Workers Builds
            |
            +--> Cloudflare GitHub App
                    |
                    +--> selected repository
```

详细无技术背景操作说明：

`docs/CLOUDFLARE_GITHUB_AUTHORIZATION.zh-CN.md`

真实 UI 字段只是 dated implementation observation。2026-09-19 pilot 的 Observed UI Mapping 见：

`docs/CLOUDFLARE_OBSERVED_UI_MAPPING.zh-CN.md`

如果 provider UI 与该映射不同，不得猜；应重新读取当前 UI、official docs 与 downstream machine contract，并通过实际 build/runtime state 反向验证。

当 AI 客户端支持 Cloudflare MCP 时，理想的人类动作只剩：

1. 授权 AI ↔ Cloudflare；
2. 授权 Cloudflare ↔ 指定 GitHub repository。

其余 Worker / Builds / trigger / preview 配置应尽量由 AI 根据机器契约完成。

## Cloudflare security profiles

Workers Builds 的原生 Git integration 与真正 per-Worker least privilege 在当前 Cloudflare 产品上不是完全同一个路径。

PPF reference 提供：

- **Profile A — Workers Builds Native**：默认参考路线，最低人工成本，但 managed user build token scope 比纯 static Worker 所需更宽；
- **Profile B — Hardened External CI**：GitHub Actions + account-owned individual-Worker `Editor` token；
- **Profile C — Future Native Granular**：等待 Workers Builds 支持 account-owned per-Worker token。

详见：

`docs/CLOUDFLARE_SECURITY_PROFILES.zh-CN.md`

正式 production cutover 前，应由项目责任人明确采用的 security profile。

其中 Profile B 在首个真实 pilot 中仅验证到 **candidate / validate-only PASS**；没有配置 account-owned deployment credential，也没有执行 Profile B production deployment，因此不得写成 production-tested。

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

## 外部 CI fallback

如果项目不能使用 Workers Builds Git integration，或项目明确要求 per-Worker least privilege，可以采用：

`GitHub Actions + Wrangler + scoped Cloudflare token`

这仍然是支持的实现，但不是本模板的默认路径。

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
8. 完成 Cloudflare OAuth / GitHub App account authorization；
9. 先通过 preview / workers.dev 验证；
10. 确认 private-source / restricted-Web 安全默认，或明确授权并记录任何有意偏离；
11. 区分 provider URL 与 canonical identity；
12. 最后才决定 Custom Domain、canonical URL 与 production cutover。

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

项目若明确选择 `access.mode: shared-password`，将 `workers/password_gate.mjs` 作为 Worker 主入口，并参考 `wrangler.password-gate.example.jsonc` 合并静态资源、Worker-first 和限速配置。将 `ratelimits[].namespace_id` 换成账户内唯一的正整数。登录密码和会话签名密钥只在 Cloudflare Worker Secrets 中直接录入；该模式会使每次静态资源请求消耗 Worker 请求额度。完整边界、故障行为和本地测试见 PPF `docs/CLOUDFLARE_ACCESS_PROFILE.zh-CN.md`。

- `publishing.yaml`：发布意图；
- `cloudflare-builds.yaml`：PPF 的 provider integration machine contract；
- `wrangler.jsonc`：Cloudflare Wrangler 原生实现配置；
- Cloudflare account settings：真实 provider-side state。

四者不应被混成同一真值源。

更高层的 provider-integration 架构研究见：

`../../docs/PROVIDER_INTEGRATION_PATTERN_RESEARCH.zh-CN.md`

该文件当前是 `AI-PROPOSED / NON-NORMATIVE`，不会改变本模板的现行 contract。

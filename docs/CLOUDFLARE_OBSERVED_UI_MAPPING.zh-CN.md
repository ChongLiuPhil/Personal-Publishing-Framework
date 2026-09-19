# Cloudflare Workers Builds — Observed UI Mapping

**Observed:** 2026-09-19  
**Status:** REFERENCE-ONLY / DATED IMPLEMENTATION NOTE  
**Scope:** PPF Quarto + Cloudflare Workers Builds reference implementation

> 本文件记录一次真实 pilot 中看到并使用过的 Cloudflare UI 映射。它不是 PPF normative specification，也不保证 Cloudflare 未来继续使用相同字段、标签、顺序或页面结构。

## 1. Authority boundary

本文件只帮助操作者把 repository machine contract 映射到 provider UI。

参数来源优先级：

1. downstream repository 当前的 `cloudflare-builds.yaml` 或等价 machine contract；
2. 当前 Cloudflare provider UI / API actual state；
3. Cloudflare current official documentation；
4. 本 dated mapping 只作为最后的历史参考。

Cloudflare 不原生读取 PPF 的 machine contract。UI 中显示的值也不会自动成为 repository durable state。

## 2. Observed field mapping

| Observed UI field | PPF reference mapping | Rule |
| --- | --- | --- |
| Project name | Worker / project name from machine contract | 不从本文件复制 pilot-specific name |
| Build command | `bash scripts/cloudflare_build.sh` | 以当前 repository machine contract 为准 |
| Deploy command | `npm run cloudflare:deploy` | 以当前 repository machine contract 为准 |
| Builds for non-production branches | enabled | 用于 preview/non-production build |
| Protect with Cloudflare Access | `publication.web.visibility` + `publication.web.access` | `public + none` 可关闭；`restricted/private` 先读取 access policy；不得从 source visibility 推断 |
| Advanced settings → Non-production branch deploy command | `npm run cloudflare:preview` | 以当前 repository machine contract 为准 |
| Advanced settings → Path | `/` for repository-root build | monorepo 必须使用真实项目路径 |
| API token | provider-managed/selected Workers Builds user token in Profile A | secret 不进入 Git、machine contract 或聊天 |
| Variables | empty unless the machine contract requires variables | 不为了填满 UI 而发明变量或 secret |

具体 Node / Wrangler / Quarto 等版本 MUST 从当前 repository machine contract / package pins 读取，不能从本 dated note 硬编码为未来项目真值。

## 3. Access control observation

2026-09-19 复核 Cloudflare current official documentation 后，Cloudflare Access 的 Worker 集成能力不应只理解为创建页面中的一个 checkbox。

当前官方文档说明可以：

- 直接保护单个 Worker；
- 只保护 preview deployments；
- 同时保护 production + preview；
- 保护特定 `workers.dev` hostname、Custom Domain 或 path。

因此 human/operator 应先读取 PPF publication contract：

~~~text
source.visibility
publication.web.authorization_state
publication.web.visibility
publication.web.access
~~~

再决定是否启用 Cloudflare Access。

以下推断无效：

~~~text
private repository => enable Access
public repository => disable Access
Worker deployed => public publication
~~~

具体 mapping 见 `docs/CLOUDFLARE_ACCESS_PROFILE.zh-CN.md`。

## 4. Production branch observation

真实 pilot 的创建 UI 中，**Production branch 不一定作为独立字段显示**。

这不构成“production branch 未配置”的证据。Pilot 完成后，实际 build/version UI 与 GitHub-side provider checks 已证明 `main` 被识别并触发预期 Workers Build。

因此如果当前创建 UI 没有显示 Production branch：

1. 不猜字段位置；
2. 完成不依赖该猜测的安全配置；
3. 检查 provider 的实际 build/deployment record；
4. 核对实际 branch / revision；
5. 必要时读取 Builds trigger settings 与 current official docs；
6. 把确认结果写回 downstream repository readiness/evidence state。

## 5. UI drift rule

如果实时 Cloudflare UI 与本文件、runbook 或旧截图不同：

- **不得猜**；
- 重新读取当前 provider UI；
- 检查 current official documentation；
- 重新读取 downstream machine contract；
- 通过 provider build/runtime evidence 验证真实结果；
- 更新 runbook / Observed UI Mapping，使 dated documentation 反映新观察。

本文件不是 human UI instruction 的 machine source of truth；machine contract 描述 repository intent，provider actual state 仍必须通过真实 provider observation/verification 得到。

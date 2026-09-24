# Cloudflare Deployment Security Profiles（PPF Reference）

**Reviewed:** 2026-09-24

本文件只描述 PPF 的 Cloudflare reference implementation，不是 PPF 合规的必需条件。

## 1. 为什么需要 Security Profile

Cloudflare 当前能力形成了一个明确的取舍：

- Workers Builds + Cloudflare Git integration 提供低人工成本、Git-triggered deployment；
- individual Worker 已可采用 `Editor` 等 granular role；
- individual-Worker granular authorization 使用 account-owned API token；
- Workers Builds 的 build credential 当前仍采用 Provider 管理的 user-token 模型；
- 因此“最方便的原生 Git 路径”和“最强的 one-Worker deployment credential 隔离”仍是两个不同 Profile。

PPF 明确记录这项取舍。

## 2. Profile A — Workers Builds Native

```text
private GitHub repository
-> Cloudflare Git integration
-> Workers Builds
-> Provider 管理的 user build credential
-> main push 后自动 build / deploy
-> 默认 Worker-scoped Access
```

Profile id：

`workers-builds-native`

这是普通新项目的**默认 Profile**。

它追求的是“每项目一次短而明确的 bootstrap”，而不是账户级零人工 Provisioning。

优点：

- 原生 Git integration；
- repository connection 完成后自动 production build / deploy；
- credential 留在 Cloudflare 侧；
- 不需要把 Cloudflare deployment token 复制到 GitHub Actions 或聊天；
- 已被现有 PPF 真实 pilot 验证；
- 可以直接使用 Worker-scoped Access，所以 account-wide Access 只是可选优化。

当前限制：

- Provider 管理的 native build credential 权限范围比纯 static Worker 日常部署真正所需更宽；
- Workers Builds 当前不能使用 Profile B 那种 account-owned one-Worker token。

PPF 标记：

`default-guided-project-setup / real-pilot-verified / broader-than-ideal-token-scope`

## 3. Profile B — Agent-Provisioned External CI

```text
platform provisioner
-> 创建/准备 private GitHub repository
-> 创建 Cloudflare Worker
-> 创建只限该 Worker / Editor 的 account-owned token
-> trusted secret broker -> GitHub Actions secrets
-> GitHub Actions -> wrangler deploy
```

Profile id：

`agent-provisioned-external-ci`

这是一个**高级可选 Profile**，适合确实优先要求 one-Worker routine deployment authority、并愿意维护额外 Provisioning infrastructure 的项目。

优点：

- Provisioning authority 与项目日常 deployment identity 分离；
- 项目 token 可以只限制到一个既有 Worker；
- routine deployment 使用 Worker `Editor`；
- Trusted Secret Broker 可以把 Cloudflare token 直接写入 GitHub Actions，明文不进入模型上下文。

代价与前置条件：

- 如果要自动创建 repository，需要已授权的 GitHub provisioning / user identity；
- Cloudflare provisioning identity 必须能创建 Worker 和 mint account-owned token；
- Cloudflare token → GitHub secret 需要 Trusted Secret Broker；
- 必须真实验证 Cloudflare granular-token issuer 的当前 policy；
- Preview automation 默认继续关闭，直到受保护 Preview 通过验收。

PPF 标记：

`optional-advanced / implemented-reference / live-provider-acceptance-pending`

当前证据边界：

- schema、可选 GitHub Actions workflow、Provisioner、reconciliation、原子 Secret Broker 编排与测试已经实现；
- 当前真实 production 证据属于 Profile A；
- 在一个干净的 Profile B Provider E2E pilot 通过以前，不得把 Profile B 写成 production-accepted。

详见 [AGENT_PROVISIONED_EXTERNAL_CI.zh-CN.md](AGENT_PROVISIONED_EXTERNAL_CI.zh-CN.md)。

## 4. Profile C — Future Native Granular

理想组合：

```text
Cloudflare Git integration
-> Workers Builds
-> account-owned token
-> individual Worker
-> Editor
```

这会同时保留 Workers Builds 的原生便利和 one-Worker account-owned deployment credential。

截至本次 reviewed 日期，Workers Builds 的 build credential 仍是 Provider 管理的 user-token 模型，因此这不是当前 active reference path。

PPF 标记：

`future-native-granular / currently-unavailable-in-workers-builds`

## 5. Deployment credential security 与 publication access 分离

Profile A / B / C 回答：

> 哪个 identity、用多大 permission scope，可以修改或部署 Worker？

它们不回答：

> 哪些 reader 可以访问已部署的 publication？

Reader access 属于 PPF `publication.web.visibility` 与 `publication.web.access`。

以下组合都可以成立：

```text
Profile A credential + public publication
Profile A credential + restricted publication
Profile B credential + public publication
Profile B credential + restricted publication
```

Deployment success 永远不自动推出 public publication。

## 6. 每项目 bootstrap 与可选平台授权

默认 Profile A 使用**每项目 bootstrap**：

- 创建或确认个人账号下 private repository；
- 需要时为该 repository 授权 Cloudflare Git integration；
- 给目标 Worker 启用 Worker-scoped Access，或复用已验证的 account-wide Access；
- 验证第一次 restricted deployment；
- 验证第二次 push 无需重新授权即可部署。

Profile B 则可以在操作者明确希望跨项目复用 Provisioning authority 时采用**平台级授权**。

体系不再要求普通新项目必须先完成平台级 Provisioning authorization。

## 7. Custom Domain 与 routine deployment 分离

无论 Profile A 还是 B，domain / DNS authority 都与普通 source deployment 分开。

不得从 repository / Worker deployment permission 推出 custom-domain permission。

## 8. PPF 安全原则

Cloudflare reference implementation SHOULD：

1. 明确记录所选 Security Profile；
2. 新 source repository 默认 private；
3. 未公开 Web output 默认 restricted + authenticated；
4. 不把 Provider 管理的 broad token 描述成 least privilege；
5. credential value 不得进入 Git、聊天、公共状态、Issue、PR 或日志；
6. 默认支持 Worker-scoped Access，同时允许复用已验证的 account-wide Access；
7. Preview 在 access protection 验证以前默认关闭；
8. public release 与 deployment success 保持独立；
9. Native 项目必须通过“第二次 push 无需重新授权也能部署”的验证，才能标记 operationally verified；
10. Provider 能力变化后重新评估这些 Profile。

对 Profile B，token 明文还必须通过 Trusted Secret Broker 保持在 model context 之外。

## 9. 选择规则

个人 GitHub 账号下的普通新项目默认使用 **Profile A — Workers Builds Native**。

只有项目明确选择更强 deployment-credential isolation、而且相应 trusted infrastructure 可用时，才使用 **Profile B — Agent-Provisioned External CI**。

只有 Workers Builds 真正支持所需 account-owned per-Worker token 且经过验证后，才使用 **Profile C**。

因此实际默认目标是：

> **每个项目只做一次短 bootstrap，之后普通 push 自动部署。**

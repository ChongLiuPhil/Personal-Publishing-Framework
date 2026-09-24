# Cloudflare Deployment Security Profiles（PPF Reference）

**Reviewed:** 2026-09-24

本文件只描述 PPF 的 Cloudflare reference implementation，不是 PPF 合规的必需条件。

## 1. 为什么需要 security profile

Cloudflare 当前能力形成了一个明确的分层：

- Workers Builds + Cloudflare GitHub App 是低人工成本的 provider-native Git integration；
- individual Worker 已可采用 `Editor` 等 granular role；
- individual-Worker granular authorization 使用 account-owned API token；
- Workers Builds 的 build credential 当前仍采用 user-token 模型；
- 因此 provider-native Workers Builds 与“日常凭据只允许修改一个 Worker”仍是两条不同安全路径。

PPF 应明确记录这个差异，而不是把某一路线描述成所有场景下都最优。

## 2. Profile A — Workers Builds Native

```text
GitHub
-> Cloudflare GitHub App
-> Workers Builds
-> provider-managed / selected user build token
-> wrangler deploy / versions upload
```

适合强调 provider-native Git integration、自动 preview/production trigger，以及不希望把部署凭据放进 GitHub 的项目。

优点：

- 原生 Git integration；
- preview 与 production trigger 简单；
- build credential 留在 Cloudflare 侧；
- 已被第一个 PPF 真实 pilot 验证。

当前限制：

- native build token 权限比纯 static Worker 日常部署所需更宽；
- Workers Builds 当前不能使用只限制到一个 Worker 的 account-owned token。

PPF 标记：

`operational-native / real-pilot-verified / broader-than-ideal-token-scope`

## 3. Profile B — Agent-Provisioned External CI

```text
platform provisioner
-> 创建 private GitHub repository
-> 验证 account-wide Access
-> 创建 Cloudflare Worker
-> 创建仅限该 Worker / Editor 的 account-owned token
-> trusted secret broker -> GitHub Actions secrets
-> GitHub Actions -> wrangler deploy
```

Profile id：

`agent-provisioned-external-ci`

当目标是“未来新项目极少重复要求人类参与，同时把日常部署权限限制到单一 Worker”时，这是首选的**新项目自动配置 Profile**。

优点：

- 平台 Provisioner 身份与项目日常部署身份分离；
- 项目部署 token 只限制到一个既有 Worker；
- routine deployment 只需要 Worker `Editor`；
- 每个新 repository 不需要再做一次 Cloudflare GitHub App 授权；
- account-wide `all_workers` Access baseline 可以让新项目从一开始保持 private/restricted；
- Secret Broker 可以把 Cloudflare token 直接安装进 GitHub Actions，明文不进入模型上下文。

代价与前置条件：

- 平台必须先拥有已授权的 GitHub provisioning principal；
- 平台必须拥有已授权的 Cloudflare provisioning principal，可创建 Worker 与 account-owned token；
- 创建项目 Worker 前必须验证 account-wide Access；
- Cloudflare token → GitHub secret 需要 trusted secret broker；
- 默认关闭 Preview 自动部署，直到受保护 Preview 通过真实验收。

PPF 标记：

`preferred-agent-provisioning / implemented-reference / live-new-project-acceptance-pending`

当前证据边界：

- schema、模板、GitHub Actions workflow、Provisioner 状态机、reconciliation 路径与测试已经实现；
- 当前仓库的真实 production 证据属于 Profile A，而不是从零新建项目的 Profile B；
- 在一个全新项目端到端 pilot 通过前，不得把 Profile B 写成 production-accepted。

详见 [AGENT_PROVISIONED_EXTERNAL_CI.zh-CN.md](AGENT_PROVISIONED_EXTERNAL_CI.zh-CN.md)。

## 4. Profile C — Future Native Granular

理想组合：

```text
Cloudflare GitHub App
-> Workers Builds
-> account-owned token
-> individual Worker
-> Editor
```

这会同时保留 Workers Builds 原生体验和 one-Worker account-owned deployment credential。

截至本次 reviewed 日期，Workers Builds 的 build credential 文档仍采用 user-token 模型，因此这还不是当前 active reference path。

PPF 标记：

`future-native-granular / currently-unavailable-in-workers-builds`

## 5. Deployment credential security 与 publication access 分离

Profile A / B / C 回答：

> 哪个身份、用多大权限，可以修改或部署 Worker？

它们不回答：

> 哪些读者可以访问已经部署的 publication？

后者属于 PPF `publication.web.visibility` 与 `publication.web.access`。

因此以下组合都可以成立：

```text
Profile A credential + public publication
Profile A credential + restricted publication
Profile B credential + public publication
Profile B credential + restricted publication
```

部署成功永远不能自动推出“已经批准公开”。

## 6. Platform authorization 与 project authorization 分离

PPF 区分：

### Platform authorization

长期复用的基础设施 authority：

- GitHub provisioning principal；
- Cloudflare provisioning principal；
- trusted secret broker。

它们应在受限的平台范围内一次授权，之后被多个项目复用。

### Project authorization

持久化的项目级决定：

- 是否允许 restricted deployment；
- 是否允许正式 public publication；
- 哪些 reader 可以访问；
- 是否可以改变 Custom Domain / canonical identity。

公开发布、扩大读者范围、扩大域名/DNS authority、付费升级默认仍是 human-reserved，除非另有明确预授权。

## 7. Custom Domain 与 routine deployment 分离

无论使用 Profile A 还是 B，domain / route provisioning 都不应成为日常部署身份的常驻权限。

推荐：

```text
temporary / platform domain provisioning authority
-> attach and verify hostname

then

routine project deployment identity
-> one Worker Editor
-> 除非部署真实改变 routing，否则不拥有 zone-route authority
```

## 8. PPF 安全原则

Cloudflare reference implementation SHOULD：

1. 明确记录采用哪个 security profile；
2. 把平台 provisioning authority 与 routine project deployment authority 分离；
3. 不把 provider-managed broad token 描述成 least privilege；
4. token 值不得进入 Git、聊天、公共状态、issue、PR 或日志；
5. 通过 trusted secret broker 让 token 明文不进入 model context；
6. 自动创建 restricted Worker 前必须验证 account-wide protection；
7. public release 与 deployment success 始终分离；
8. 保留 provider-native Profile，供更重视 convenience 的项目明确选择；
9. Provider 能力变化后重新评估这些 Profile。

## 9. 选择规则

完成平台 bootstrap 后，未来 Agent 自动配置的新项目优先 **Profile B**。

如果项目明确更重视 Workers Builds provider-native Git integration，而可以接受较宽 build-token scope，则采用 **Profile A**。

只有在 Workers Builds 真正支持所需的 account-owned per-Worker token，并经过真实验证后，才采用 **Profile C**。

第一个全新 Profile B 项目仍必须通过 live acceptance，仓库才能把该 Profile 标成 production-accepted。

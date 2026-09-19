# Cloudflare Deployment Security Profiles（PPF Reference）

**Reviewed:** 2026-09-19

本文件只描述 PPF 的 Cloudflare reference implementation，不是 PPF 合规的必需条件。

## 1. 为什么需要 security profile

真实 pilot 证明：

- Cloudflare Workers Builds + GitHub App 是低人工操作、原生 preview/production trigger 的稳定路线；
- Cloudflare 当前 Workers 权限模型已经支持 individual Worker + `Editor`；
- 但 Workers Builds 当前只支持 **user token**；
- granular Wrangler authorization 的 individual-Worker token 路线依赖 **account-owned API token**；
- 因此“Workers Builds 原生体验”和“真正 per-Worker least privilege”在当前产品上不能完全同时实现。

PPF reference implementation 不应掩盖这个 trade-off。

## 2. Profile A — Workers Builds Native

```text
GitHub
-> Cloudflare GitHub App
-> Workers Builds
-> Cloudflare-managed / selected user build token
-> wrangler deploy / versions upload
```

适合：

- 希望最少人工配置；
- 希望保留 provider-native Git integration；
- 希望自动 production / preview builds；
- 不希望把 Cloudflare deployment secret 放进 GitHub。

优点：

- 原生 Git integration；
- preview 与 production trigger 简单；
- token 保存在 Cloudflare 侧；
- 已被 PPF 第一个真实 pilot 验证。

当前限制：

- Cloudflare 自动创建的默认 build token 权限比纯 static Worker 日常 deploy 所需更宽；
- Workers Builds 当前不支持 account-owned token，因此不能采用最新 per-Worker account-owned `Editor` token。

PPF 标记：

`reference-default / operational / broader-than-ideal-token-scope`

## 3. Profile B — Hardened External CI

```text
GitHub Actions
-> account-owned Cloudflare API token
-> individual Worker
-> Editor
-> wrangler deploy
```

适合：

- 明确要求 per-Worker least privilege；
- 愿意接受更多 secret management 和 CI 配置；
- 可以由 external CI 接管 deployment。

优点：

- 可以把 token 限制到一个既有 Worker；
- routine deployment 只需要 `Editor`；
- 不需要 KV / R2 / D1 权限；
- 不需要 routine all-zone route write。

代价：

- 需要创建 account-owned token；
- 需要把 token 和 account ID 安全存进 CI secret store；
- production / preview trigger semantics 需要自行实现并验证；
- 初次人类配置步骤更多。

PPF 标记：

`supported-hardened-alternative / pilot-candidate-validate-only`

当前真实 pilot 的证据边界：

- candidate workflow 的 repository/build validation：PASS；
- PR 场景中的 credential / preview / production deployment steps：SKIPPED；
- account-owned per-Worker token：未配置；
- Profile B production deployment：未执行；
- 因此 **不得** 把 Profile B 描述为 production-tested。

## 4. Profile C — Future Native Granular

理想组合：

```text
Cloudflare GitHub App
-> Workers Builds
-> account-owned token
-> individual Worker
-> Editor
```

它同时保留：

- Workers Builds 原生体验；
- provider-managed preview / production trigger；
- per-Worker least privilege。

截至本文件 reviewed 日期，Cloudflare Workers Builds 文档仍说明仅支持 user token，account-owned token support 尚未成为当前能力。

PPF 标记：

`future-preferred / currently-unavailable`

## 5. Custom Domain 与 daily deployment 分离

无论使用 A 或 B：

Custom Domain / Route provisioning 不应成为 routine deploy credential 的常驻权限。

推荐：

```text
temporary domain provisioning authority
-> Worker access
-> affected zone Workers Routes Write
-> attach/verify domain

then

routine deployment identity
-> no zone-route write unless deployment actually changes routing
```

## 6. PPF 安全原则

Cloudflare reference implementation SHOULD：

1. 明确记录采用哪个 security profile；
2. 不把 provider-managed broad token 描述成 least privilege；
3. 不把 token secret 写入 Git、聊天或 machine contract；
4. 不为了理论 hardening 在没有 rollback path 时破坏已验证 pipeline；
5. 当 provider-native integration 无法满足所需 credential scope 时，明确提供 external-CI hardened alternative；
6. provider 产品能力变化后重新评估 profile。

## 7. 选择规则

默认采用 **Profile A** 只表示 reference convenience default，不代表它在所有安全环境中最优。

如果项目在 production 前要求：

> routine deploy credential 必须只能修改一个既有 Worker

则应该采用 **Profile B**，直到 Profile C 被 Cloudflare Workers Builds 正式支持。

最终 production security profile 应由项目责任人确认。

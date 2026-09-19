# Cloudflare Access Publication Profile（PPF Reference）

**Reviewed:** 2026-09-19  
**Status:** REFERENCE-ONLY / DATED PROVIDER MAPPING  
**Scope:** PPF publication visibility / access policy on Cloudflare Workers

> 本文件把 PPF 的 provider-neutral publication semantics 映射到当前 Cloudflare Workers / Cloudflare Access 产品能力。它不是 PPF normative specification。

## 1. PPF semantic boundary

PPF core 区分：

- source / repository visibility；
- publication authorization；
- publication visibility；
- access policy；
- canonical publication identity；
- delivery provider / provider endpoint。

Cloudflare reference implementation 不得重新把这些对象合并。

特别是：

~~~text
private repository
!= private website

restricted website
!= unpublished website

workers.dev reachable
!= canonical identity
~~~

## 2. Public publication

PPF contract 示例：

~~~yaml
publication:
  web:
    authorization_state: authorized
    visibility: public
    access:
      mode: none
~~~

Cloudflare reference mapping：

- Worker / Custom Domain 可以保持公开；
- 不需要为了“配置完整”而启用 Access；
- 如果 `workers.dev` 保持 enabled，它本身是 provider URL；
- provider URL 是否同时是 canonical identity，由项目单独记录和批准。

## 3. Restricted publication

PPF contract 示例：

~~~yaml
publication:
  web:
    authorization_state: authorized
    visibility: restricted
    access:
      mode: authenticated
      implementation: cloudflare-access
      policy_ref: docs/access-policy.md
~~~

Cloudflare 当前 Workers 文档支持：

- 直接对一个 Worker 启用 Access；
- 只保护 preview deployments；
- 同时保护 production + preview deployments；
- 对特定 hostname / `workers.dev` / Custom Domain / path 建立 Access application；
- 用 Access policy 决定哪些访问者可以登录。

因此，restricted publication 可以保持“正式已发布”，同时把 audience 限制在通过 Access policy 的访问者。

## 4. Private publication

PPF 的 `visibility: private` 不要求唯一 Cloudflare 实现。

可用 reference approaches 包括：

- Worker-level Access，只允许项目定义的极小 audience；
- hostname-level Access，只允许 selected audience；
- 不暴露一般 public route；
- 在尚未形成安全 access policy 时保持 deployment staged / disabled。

项目必须明确自己所说的 `private` 是“仅项目成员”“仅本人”“特定名单”还是其他边界。

## 5. Access mode mapping

PPF → Cloudflare reference mapping：

| PPF access mode | Cloudflare reference |
| --- | --- |
| `none` | 不启用 Access，或明确 public bypass |
| `authenticated` | Cloudflare Access + authentication policy |
| `selected-audience` | Cloudflare Access + email / domain / group / other allow policy |
| `other` | 项目记录 provider-specific implementation |

PPF core 不规定 password、OTP、SSO 或具体 identity provider。

Cloudflare Access 当前可以使用其支持的 authentication methods；例如 One-Time PIN 是一种 provider-specific choice，不应写进 PPF normative vocabulary。

## 6. Worker-level vs hostname-level protection

当前 Cloudflare Workers Access 支持两种重要范围：

### Worker-level

Access policy 绑定到 Worker，可以覆盖其关联的 production / preview endpoints。

适合：

- publication 本身整体 restricted/private；
- 不希望以后增加 Custom Domain 时遗漏 access protection。

### Hostname/path-level

只保护一个指定 hostname、Custom Domain、`workers.dev` hostname 或 path。

适合：

- 同一个 Worker 同时承载 public 与 restricted surface；
- 只保护 preview、admin path 或某个特定 hostname。

选择哪一种属于 provider implementation decision，不改变 PPF contract 的 visibility/access semantics。

## 7. Canonical identity

Cloudflare reference 必须分别记录：

~~~text
provider_url
canonical_identity
~~~

例如：

~~~yaml
deployment:
  web:
    provider_url: https://example-account.workers.dev
    canonical_identity:
      type: provider-native
      url: https://example-account.workers.dev
~~~

未来迁移到自有域名时：

~~~yaml
deployment:
  web:
    provider_url: https://example-account.workers.dev
    canonical_identity:
      type: custom-domain
      url: https://example.org
~~~

改变 canonical identity 需要显式 cutover；不能因为 Custom Domain 或 `workers.dev` 已可访问就自动更新。

Cloudflare 当前官方文档建议 production Worker 优先使用 route 或 Custom Domain，而不是把 `workers.dev` 当作所有 production 场景的长期默认。因此 PPF reference 把 `workers.dev` 视为稳定的 provider-native endpoint，而不把它定义为永久 canonical identity。

## 8. Secret boundary

Publication contract / access metadata MAY 记录：

- access mode；
- provider implementation name；
- policy file / policy identifier reference；
- audience category；
- verified state。

不得记录：

- password；
- API token；
- private key；
- session secret；
- recovery code；
- one-time login code。

## 9. Current official references

Reviewed against current Cloudflare documentation on 2026-09-19:

- Cloudflare Workers — Cloudflare Access:
  https://developers.cloudflare.com/workers/configuration/cloudflare-access/
- Cloudflare Workers — workers.dev:
  https://developers.cloudflare.com/workers/configuration/routing/workers-dev/
- Cloudflare One — One-time PIN login:
  https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/one-time-pin/

If current provider behavior differs from this dated note, re-read the official documentation and provider actual state rather than guessing.

# Cloudflare Access Publication Profile (PPF Reference)

**Reviewed:** 2026-09-19  
**Status:** REFERENCE-ONLY / DATED PROVIDER MAPPING  
**Scope:** PPF publication visibility / access policy on Cloudflare Workers

> This file maps provider-neutral PPF publication semantics to current Cloudflare Workers / Cloudflare Access capabilities. It is not part of the PPF normative specification.

## 1. PPF semantic boundary

PPF core distinguishes:

- source / repository visibility;
- publication authorization;
- publication visibility;
- access policy;
- canonical publication identity;
- delivery provider / provider endpoint.

The Cloudflare reference implementation must not collapse these objects back together.

In particular:

~~~text
private repository
!= private website

restricted website
!= unpublished website

workers.dev reachable
!= canonical identity
~~~

## 2. Public publication

PPF contract example:

~~~yaml
publication:
  web:
    authorization_state: authorized
    visibility: public
    access:
      mode: none
~~~

Cloudflare reference mapping:

- the Worker / Custom Domain may remain public;
- Access need not be enabled merely to make configuration look complete;
- if `workers.dev` remains enabled, it is a provider URL;
- whether that provider URL is also canonical identity is a separate project decision.

## 3. Restricted publication

PPF contract example:

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

Current Cloudflare Workers documentation supports:

- enabling Access directly on one Worker;
- protecting preview deployments only;
- protecting production + preview deployments together;
- creating Access applications for a specific hostname / `workers.dev` / Custom Domain / path;
- using Access policy to determine which visitors may sign in.

A restricted publication can therefore remain a formal, authorized publication while limiting its audience to visitors satisfying the Access policy.

## 4. Private publication

PPF `visibility: private` does not require one unique Cloudflare implementation.

Reference approaches include:

- Worker-level Access with a very small project-defined audience;
- hostname-level Access with a selected audience;
- no generally public route;
- keeping deployment staged / disabled until a safe access policy exists.

The project must define whether `private` means project members only, owner only, a named list, or another boundary.

## 5. Access mode mapping

PPF → Cloudflare reference mapping:

| PPF access mode | Cloudflare reference |
| --- | --- |
| `none` | no Access, or an explicit public bypass |
| `authenticated` | Cloudflare Access + authentication policy |
| `selected-audience` | Cloudflare Access + email / domain / group / other allow policy |
| `other` | project-recorded provider-specific implementation |

PPF core does not prescribe passwords, OTP, SSO, or a concrete identity provider.

Cloudflare Access may use supported authentication methods. One-Time PIN, for example, is a provider-specific choice and does not belong in the PPF normative vocabulary.

## 6. Worker-level vs hostname-level protection

Current Cloudflare Workers Access supports two important scopes.

### Worker-level

Access policy attaches to the Worker and can cover associated production / preview endpoints.

Appropriate when:

- the publication as a whole is restricted/private;
- later addition of a Custom Domain should not accidentally bypass protection.

### Hostname/path-level

Protect only a specified hostname, Custom Domain, `workers.dev` hostname, or path.

Appropriate when:

- one Worker exposes both public and restricted surfaces;
- only preview, an admin path, or one hostname should be protected.

Choosing the scope is a provider implementation decision and does not alter the PPF contract's visibility/access semantics.

## 7. Canonical identity

Cloudflare reference state records these separately:

~~~text
provider_url
canonical_identity
~~~

For example:

~~~yaml
deployment:
  web:
    provider_url: https://example-account.workers.dev
    canonical_identity:
      type: provider-native
      url: https://example-account.workers.dev
~~~

A later custom-domain migration becomes:

~~~yaml
deployment:
  web:
    provider_url: https://example-account.workers.dev
    canonical_identity:
      type: custom-domain
      url: https://example.org
~~~

Changing canonical identity requires explicit cutover. It is not updated merely because a Custom Domain or `workers.dev` endpoint becomes reachable.

Current Cloudflare documentation recommends a route or Custom Domain for production Workers rather than treating `workers.dev` as the long-term default for every production context. The PPF reference therefore treats `workers.dev` as a stable provider-native endpoint without making it the permanent canonical identity.

## 8. Secret boundary

Publication contract / access metadata MAY record:

- access mode;
- provider implementation name;
- policy-file / policy-identifier reference;
- audience category;
- verified state.

They must not record:

- passwords;
- API tokens;
- private keys;
- session secrets;
- recovery codes;
- one-time login codes.

## 9. Current official references

Reviewed against current Cloudflare documentation on 2026-09-19:

- Cloudflare Workers — Cloudflare Access:
  https://developers.cloudflare.com/workers/configuration/cloudflare-access/
- Cloudflare Workers — workers.dev:
  https://developers.cloudflare.com/workers/configuration/routing/workers-dev/
- Cloudflare One — One-time PIN login:
  https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/one-time-pin/

If current provider behavior differs from this dated note, re-read official documentation and provider actual state rather than guessing.

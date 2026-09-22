# Cloudflare Access Publication Profile (PPF Reference)

**Reviewed:** 2026-09-20  
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
| `shared-password` | PPF Worker gate + server-side Cloudflare secrets; opt in per project |
| `other` | project-recorded provider-specific implementation |

PPF defines the shared-password access mode; password/session behavior remains a provider implementation detail. Other modes do not prescribe OTP, SSO, or a concrete identity provider.

For the current Inquiry Publishing Stack reference deployment, `policy_ref: shared-reader-access` maps to one reusable Cloudflare Access policy. The preferred human-reader implementation is an explicit email allowlist plus One-Time PIN, with a 24h initial policy/application session. Reader identities and provider IDs remain private provider state.

Current Cloudflare Access policy selectors are identity/policy oriented (for example email, login method, group, device posture, service token). A generic static shared password is not a native Access selector. Use the separate PPF Worker gate when a project explicitly selects shared-password mode; never persist its value in Git.

Cloudflare Access may use supported authentication methods. One-Time PIN is a provider-specific choice and does not belong in the PPF normative vocabulary.

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

## 9. Optional project shared-password profile

`providers/cloudflare/password_gate.mjs` is the PPF reference implementation for projects that explicitly select shared-password access. It intercepts every asset only when Wrangler has `assets.run_worker_first: true`, including direct file and JSON requests. The password and session signing key are Cloudflare Worker secrets only. The module fails closed when a secret or binding is missing, issues signed 12-hour Secure/HttpOnly/SameSite cookies, invalidates sessions when either secret is rotated, and applies a Workers Rate Limiting binding to login attempts. Authenticated static responses use `private, no-store`.

Cloudflare's Workers Rate Limiting API is per Cloudflare location and permissive/eventually consistent. It can also group readers behind a shared public IP. It reduces casual repeated guessing but is not a global abuse-prevention or accounting system. Give every project a distinct rate-limit namespace ID. The broader production security caveats remain: shared-password access does not provide individual reader identity, revocation, or auditability; prefer Access for an approved named audience.

The secret names are `PPF_ACCESS_PASSWORD` and `PPF_SESSION_SIGNING_KEY`. Store the values directly as Worker secrets; never put values in `publishing.yaml`, source, workflow variables, evidence, or chat. See the opt-in sample at `providers/cloudflare/password_gate.wrangler.jsonc` and tests at `providers/cloudflare/tests/password_gate.test.mjs`.

Current Workers references:

- Static Assets Worker-first routing: https://developers.cloudflare.com/workers/static-assets/binding/
- Workers best practices and timing-safe comparison: https://developers.cloudflare.com/workers/best-practices/workers-best-practices/
- Workers Rate Limiting locality and accuracy: https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/

## 10. Current official Access references

Reviewed against current Cloudflare documentation on 2026-09-20:

- Cloudflare Workers — Cloudflare Access:
  https://developers.cloudflare.com/workers/configuration/cloudflare-access/
- Cloudflare Workers — workers.dev:
  https://developers.cloudflare.com/workers/configuration/routing/workers-dev/
- Cloudflare One — One-time PIN login:
  https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/one-time-pin/
- Cloudflare One — Access policies:
  https://developers.cloudflare.com/cloudflare-one/access-controls/policies/
- Cloudflare One — Manage Access policies:
  https://developers.cloudflare.com/cloudflare-one/access-controls/policies/policy-management/
- Cloudflare API — Access applications and policies:
  https://developers.cloudflare.com/api/resources/zero_trust/subresources/access/subresources/applications/
  https://developers.cloudflare.com/api/resources/zero_trust/subresources/access/subresources/policies/

If current provider behavior differs from this dated note, re-read official documentation and provider actual state rather than guessing.

# Cloudflare Workers Builds — Observed UI Mapping

**Observed:** 2026-09-19  
**Status:** REFERENCE-ONLY / DATED IMPLEMENTATION NOTE  
**Scope:** PPF Quarto + Cloudflare Workers Builds reference implementation

> This file records UI mapping actually observed and used in a real pilot. It is not part of the PPF normative specification and does not claim that Cloudflare will preserve the same fields, labels, order, or page structure.

## 1. Authority boundary

This document only helps an operator map repository machine-contract intent into provider UI.

Parameter precedence:

1. the downstream repository's current `cloudflare-builds.yaml` or equivalent machine contract;
2. current Cloudflare provider UI / API actual state;
3. current official Cloudflare documentation;
4. this dated mapping only as historical reference.

Cloudflare does not natively consume the PPF machine contract. Values displayed in UI also do not automatically become repository durable state.

## 2. Observed field mapping

| Observed UI field | PPF reference mapping | Rule |
| --- | --- | --- |
| Project name | Worker / project name from machine contract | do not copy a pilot-specific name from this file |
| Build command | `bash scripts/cloudflare_build.sh` | current repository machine contract governs |
| Deploy command | `wrangler deploy` | fixed operation; do not route provider credentials through an npm script |
| Builds for non-production branches | enabled | supports preview/non-production builds |
| Protect with Cloudflare Access | `publication.web.visibility` + `publication.web.access` | may be off for `public + none`; read the access policy for `restricted/private`; do not infer from source visibility |
| Advanced settings → Non-production branch deploy command | `wrangler versions upload` | fixed operation; do not route provider credentials through an npm script |
| Advanced settings → Path | `/` for repository-root build | a monorepo must use the actual project path |
| API token | provider-managed/selected Workers Builds user token in Profile A | secret never enters Git, machine contract, or chat |
| Variables | empty unless required by the machine contract | do not invent variables or secrets merely to fill UI |

Concrete Node / Wrangler / Quarto versions MUST be read from the current repository machine contract / package pins rather than hard-coded from this dated note as future project truth.

## 3. Access-control observation

After review of current Cloudflare official documentation on 2026-09-19, Worker Access should not be understood merely as a checkbox on the creation page.

Current documentation supports:

- protecting one Worker directly;
- protecting preview deployments only;
- protecting production + preview together;
- protecting a specific `workers.dev` hostname, Custom Domain, or path.

The operator should therefore read the PPF publication contract first:

~~~text
source.visibility
publication.web.authorization_state
publication.web.visibility
publication.web.access
~~~

and only then decide whether Cloudflare Access should be enabled.

These inferences are invalid:

~~~text
private repository => enable Access
public repository => disable Access
Worker deployed => public publication
~~~

See `docs/CLOUDFLARE_ACCESS_PROFILE.md` for the reference mapping.

## 4. Production branch observation

In the real pilot creation UI, **Production branch was not guaranteed to appear as a separate field**.

That is not evidence that the production branch is unconfigured. After setup, actual build/version UI and GitHub-side provider checks established that `main` was recognized and triggered the expected Workers Build.

If the current creation UI does not show Production branch:

1. do not guess where the field moved;
2. complete safe configuration that does not depend on that guess;
3. inspect the provider's actual build/deployment record;
4. verify the actual branch / revision;
5. inspect Builds trigger settings and current official docs when needed;
6. write the verified result back to downstream repository readiness/evidence state.

## 5. UI drift rule

If the live Cloudflare UI differs from this file, the runbook, or an older screenshot:

- **do not guess**;
- re-read the current provider UI;
- check current official documentation;
- re-read the downstream machine contract;
- verify the actual result through provider build/runtime evidence;
- update the runbook / Observed UI Mapping so dated documentation reflects the new observation.

This file is not a machine source of truth for human UI instructions. The machine contract describes repository intent; provider actual state must still be established by real provider observation and verification.

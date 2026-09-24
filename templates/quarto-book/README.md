# PPF Quarto Book Reference Template

This directory is an executable Quarto reference implementation of the **Personal Publishing Framework (PPF)**.

It demonstrates:

```text
QMD / Markdown / BibTeX
        |
        +--> GitHub Actions
        |      validate -> make web-publish-check
        |      deploy   -> durable publication authorization gate
        |               -> project-scoped Worker Editor credential
        |               -> wrangler deploy
        |
        +--> Cloudflare Worker
        |      account-wide Access baseline
        |      restricted by default
        |
        +--> explicit request
               EPUB / PDF / DOCX / LaTeX
```

These technologies are a reference implementation, not PPF requirements.

## One canonical Web publication gate

The repository centralizes Web build and validation in:

`make web-publish-check`

It performs:

1. publication-contract validation;
2. Quarto Web rendering;
3. rendered Web-artifact validation.

GitHub Actions and Cloudflare Workers Builds both call the same gate so validation logic does not drift across CI providers.

## GitHub Actions responsibility

`.github/workflows/web.yml` performs independent validation:

- checkout;
- Python;
- Quarto;
- `make web-publish-check`.

`.github/workflows/deploy-cloudflare.yml` is the authorized production deployment workflow for the preferred external-CI profile. It reads the durable `publishing.yaml` state, remains a no-op until Web deployment is both authorized and enabled, then builds and runs `wrangler deploy` with repository-scoped Cloudflare secrets.

`.github/workflows/cloudflare-contract-ci.yml` validates the locked Cloudflare/Wrangler build contract from a clean runner. It does **not** deploy.

## Cloudflare integration machine contract

`cloudflare-builds.yaml` records the account-side configuration expected by the PPF reference implementation:

- Git repository;
- production branch;
- non-production branch builds;
- root directory;
- build command;
- deploy command;
- preview deploy command;
- Worker name;
- toolchain versions;
- connection/readiness state;
- security policy.

**Cloudflare does not automatically consume this YAML file.**

It is a PPF machine contract used by the Agent/provisioner and CI. In the preferred external-CI profile it describes GitHub Actions deployment, the secret-broker boundary, Worker creation authority, and the Access precondition; in the native profile it can still describe Workers Builds configuration.

## Source visibility / publication visibility / access / canonical identity

The reference template now demonstrates four independent state layers:

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

These are the safe reference defaults for newly configured original or unpublished work: private source, restricted Web, authenticated access, and no production publication authorization yet. A project may later choose a different combination explicitly.

Valid downstream combinations include:

~~~text
private source + public Web
private source + restricted Web
public source + restricted Web
restricted Web + authenticated access
~~~

Do not make a Web publication private merely because the repository is private, and do not make a reachable Worker endpoint canonical merely because it exists.

When restricted/private Web access is needed, the Cloudflare reference may use Cloudflare Access. See:

`docs/CLOUDFLARE_ACCESS_PROFILE.md`

That file is a dated provider reference, not a PPF conformance requirement.

## Recommended platform connection

For future Agent-provisioned projects, the preferred route is:

```text
one GitHub provisioning authorization
+ one Cloudflare provisioning authorization
        |
        v
Project Provisioner
-> private repository
-> protected Worker
-> secret broker
-> GitHub Actions deploy
```

A new repository inside the already approved scope should not require another Cloudflare GitHub App authorization.

See:

- `docs/AGENT_PROVISIONED_EXTERNAL_CI.md`
- `docs/CLOUDFLARE_GITHUB_AUTHORIZATION.md`

Live UI fields are only dated implementation observations. The Observed UI Mapping from the 2026-09-19 pilot is documented in:

`docs/CLOUDFLARE_OBSERVED_UI_MAPPING.md`

If provider UI differs, do not guess. Re-read the current UI, official documentation, and downstream machine contract, then verify through actual build/runtime state.

When the execution environment supports Cloudflare MCP/API and GitHub App/API capabilities, the human role should normally reduce to the two platform authorizations. The Agent then provisions later projects inside those approved scopes. Public release, new reader scope, new domain/DNS authority, and permission expansion remain separate human gates.

## Cloudflare security profiles

Native Workers Builds Git integration and true per-Worker least privilege are not currently the same Cloudflare path.

The PPF reference provides:

- **Profile A — Workers Builds Native**: operational provider-native profile with real pilot evidence, but broader build-token scope;
- **Profile B — Agent-Provisioned External CI**: preferred new-project automation profile; GitHub Actions + account-owned individual-Worker `Editor` token through a trusted secret broker;
- **Profile C — Future Native Granular**: future native combination once Workers Builds supports account-owned per-Worker tokens.

See:

`docs/CLOUDFLARE_SECURITY_PROFILES.md`

The template now selects Profile B for new Agent-provisioned projects. Repository implementation and CI validation are present, but no clean new-project Profile B production acceptance has yet been recorded; it must not be described as production-tested until that pilot succeeds.

## Runtime verification reference

Build success is not runtime success. After provider integration, a project can use the read-only helper:

~~~bash
python scripts/verify_public_site.py https://example.invalid \
  --path / \
  --path /representative-page.html \
  --expect "Expected visible text"
~~~

The helper verifies HTTP 200, UTF-8 pages, representative paths, optional content markers, and a bounded sample of local assets.

It does **not** replace:

- expected Git/source revision checks against provider build metadata;
- project-specific navigation/content assertions;
- incumbent-production health checks during migration;
- explicit canonical production cutover.

Downstream projects should add those gates for their actual structure.

## External CI is the new-project provisioning default

The installable template now uses:

`GitHub Actions + Wrangler + account-owned individual-Worker Editor token`

for Agent-provisioned new projects. Workers Builds Native remains supported as an explicit provider-native profile and as the currently verified real pilot.

Any token:

- must not enter Git;
- must not be written into chat or README files;
- should use the least privilege needed;
- should separate one-time provisioning authority from recurring deployment authority.

## Pinned toolchain

The template pins:

- Node 24 via `.nvmrc`;
- Wrangler 4.135.0 via `package.json`;
- Quarto 1.10.18 via `scripts/ensure_quarto.sh`.

The Cloudflare build wrapper does not assume the provider preinstalls Quarto. It downloads the pinned release and verifies SHA-256 before use.

## On-demand formats

`.github/workflows/build-publication.yml` runs only through `workflow_dispatch`.

One explicit request selects EPUB, PDF, DOCX, or LaTeX. The workflow verifies that the requested artifact exists before uploading it as a GitHub Actions artifact.

Project-specific fonts, TeX packages, or other heavy dependencies belong in the downstream project when needed.

**Build is not Release, and Release is not external Publish.**

## Required customization

Before adopting the template:

1. replace the book title and author in `_quarto.yml`;
2. replace project id/title values in `publishing.yaml`;
3. replace `OWNER/REPOSITORY` and Worker name in `cloudflare-builds.yaml`;
4. replace the Worker name in `wrangler.jsonc`;
5. add project-specific source/output validation;
6. replace sample QMD, bibliography, and assets;
7. pass the GitHub reference contract CI;
8. verify the platform GitHub and Cloudflare provisioning principals and the account-wide Access baseline;
9. let the trusted secret broker install the project-scoped Worker deployment credential without exposing its value;
10. run the restricted workers.dev deployment and verify anonymous denial before enabling previews;
11. confirm the private-source / restricted-Web safety defaults, or explicitly authorize and record any intended deviation;
12. distinguish provider URL from canonical identity;
13. only then decide Custom Domain, canonical URL, and public cutover.

## Output directories

```text
_book/
  continuous Web artifact

_publication/
  epub/
  pdf/
  docx/
  latex/
```

These are derived outputs and are ignored by Git by default.

## Publication contract vs provider implementation

Infrastructure authentication uses Cloudflare Access. Do not add a project-level shared-password or session gate for publication access; application authentication belongs only to projects with real application user accounts. See the PPF Cloudflare Access profile for account-wide, Worker-level, and preview protection.

- `publishing.yaml`: publication intent;
- `cloudflare-builds.yaml`: PPF provider-integration machine contract;
- `wrangler.jsonc`: native Cloudflare Wrangler implementation config;
- Cloudflare account settings: real provider-side state.

These should not be collapsed into a single source of truth.

For the higher-level provider-integration architecture research, see:

`../../docs/PROVIDER_INTEGRATION_PATTERN_RESEARCH.md`

That file is currently `AI-PROPOSED / NON-NORMATIVE` and does not change this template's active contract.

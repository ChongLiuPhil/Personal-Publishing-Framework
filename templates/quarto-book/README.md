# PPF Quarto Book Reference Template

This directory is an executable Quarto reference implementation of the **Personal Publishing Framework (PPF)**.

It demonstrates:

```text
QMD / Markdown / BibTeX
        |
        +--> GitHub Actions
        |      validate -> make web-publish-check
        |
        +--> Cloudflare Workers Builds
        |      connected private GitHub repository
        |      build -> deploy on main push
        |      Worker-scoped Access by default
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

`.github/workflows/deploy-cloudflare.yml` is retained for the optional advanced external-CI profile. It is not the default production path. The default path uses Cloudflare Workers Builds after the project repository has been connected once.

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

It is a PPF machine contract used by the Agent and CI. The reference default describes Workers Builds Git integration, the one-time project connection, Worker-scoped Access, and preview safety. The optional `external_ci` block preserves the hardened GitHub Actions + Trusted Secret Broker profile.

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

## Recommended project connection

For an ordinary new project, the preferred route is:

```text
private GitHub repository
-> one project-level Cloudflare Git authorization
-> Workers Builds
-> Worker-scoped Access
-> verify first restricted deployment
-> make a second push
-> confirm automatic redeployment without renewed authorization
```

This deliberately allows a short human bootstrap once per project. Account-wide automation is optional, not required.

See:

- `docs/PER_PROJECT_GITHUB_CLOUDFLARE_SETUP.md`
- `docs/CLOUDFLARE_GITHUB_AUTHORIZATION.md`

Live UI fields are dated implementation observations. If provider UI differs, do not guess: re-read current official documentation and verify against actual build/runtime state.

## Cloudflare security profiles

Native Workers Builds Git integration and true per-Worker least-privilege deployment credentials are still different Cloudflare paths.

The PPF reference provides:

- **Profile A — Workers Builds Native**: **default guided project setup**, real-pilot verified, provider-managed build credential with broader-than-ideal scope;
- **Profile B — Agent-Provisioned External CI**: optional advanced profile using GitHub Actions + account-owned individual-Worker `Editor` token through a trusted Secret Broker;
- **Profile C — Future Native Granular**: future native combination if Workers Builds gains the required account-owned per-Worker credential path.

The installable template selects Profile A by default. Profile B remains implemented but must not be described as production-accepted until its live Provider acceptance is complete.

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

## Workers Builds Native is the new-project default

The installable template now uses the native Workers Builds Git integration for ordinary new projects. The user may complete one short project connection and Access setup; after that, normal pushes should deploy automatically.

The advanced external-CI profile remains available when stronger credential isolation is worth the additional infrastructure.

Any credential:

- must not enter Git;
- must not be written into chat or README files;
- should use the least privilege supported by the selected profile.

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
8. connect the private repository to Cloudflare Workers Builds and authorize that repository if prompted;
9. protect the Worker with Worker-scoped Access, or verify an already-existing account-wide Access policy;
10. run the first restricted deployment and verify anonymous denial before enabling previews;
11. make a second harmless push and confirm Workers Builds redeploys without renewed authorization;
12. confirm the private-source / restricted-Web safety defaults, or explicitly authorize and record any intended deviation;
13. distinguish provider URL from canonical identity;
14. only then decide Custom Domain, canonical URL, and public cutover.

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

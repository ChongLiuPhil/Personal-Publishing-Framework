# PPF Quarto Book Reference Template

This directory is an executable Quarto reference implementation of the **Personal Publishing Framework (PPF)**.

It demonstrates:

```text
QMD / Markdown / BibTeX
        |
        +--> GitHub Actions
        |      make web-publish-check
        |      (independent quality validation)
        |
        +--> Cloudflare Workers Builds
        |      bash scripts/cloudflare_build.sh
        |        -> pinned Quarto
        |        -> make web-publish-check
        |      preview -> wrangler versions upload
        |      main    -> wrangler deploy
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

`.github/workflows/web.yml` performs independent validation only:

- checkout;
- Python;
- Quarto;
- `make web-publish-check`.

It does **not** hold a Cloudflare token and does not perform Cloudflare production deployment.

`.github/workflows/cloudflare-contract-ci.yml` additionally simulates the Workers Builds environment with:

- Node 24;
- Wrangler 4.135.0;
- Python;
- checksum-verified Quarto 1.10.18;
- `make cloudflare-build`.

This workflow also does **not** deploy. It proves that the template can build from a clean runner.

## Workers Builds machine contract

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

It is a PPF machine contract that an AI agent or human operator applies to Cloudflare Workers Builds.

## Recommended account connection

The default reference route is:

```text
AI Agent
   |
   +--> Cloudflare OAuth / MCP

Cloudflare
   |
   +--> Workers Builds
            |
            +--> Cloudflare GitHub App
                    |
                    +--> selected repository
```

See the nontechnical authorization guide:

`docs/CLOUDFLARE_GITHUB_AUTHORIZATION.md`

When the AI client supports Cloudflare MCP, the ideal human role is reduced to:

1. authorize AI ↔ Cloudflare;
2. authorize Cloudflare ↔ the selected GitHub repository.

The AI should then configure Worker / Builds / triggers / preview state from the machine contract where its client exposes the required Cloudflare tools.

## Cloudflare security profiles

Native Workers Builds Git integration and true per-Worker least privilege are not currently the same Cloudflare path.

The PPF reference provides:

- **Profile A — Workers Builds Native**: reference default with minimal manual setup, but a broader managed user-token scope than a pure static Worker needs;
- **Profile B — Hardened External CI**: GitHub Actions + account-owned individual-Worker `Editor` token;
- **Profile C — Future Native Granular**: the preferred native combination once Workers Builds supports account-owned per-Worker tokens.

See:

`docs/CLOUDFLARE_SECURITY_PROFILES.md`

The project owner should explicitly select the production security profile before final cutover.

## External-CI fallback

If a project cannot use Workers Builds Git integration, or explicitly requires per-Worker least privilege, it may use:

`GitHub Actions + Wrangler + scoped Cloudflare token`

This remains supported but is not the default template path.

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
8. complete Cloudflare OAuth / GitHub App account authorization;
9. validate preview / workers.dev first;
10. only then decide Custom Domain, canonical URL, and production cutover.

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

- `publishing.yaml`: publication intent;
- `cloudflare-builds.yaml`: PPF provider-integration machine contract;
- `wrangler.jsonc`: native Cloudflare Wrangler implementation config;
- Cloudflare account settings: real provider-side state.

These should not be collapsed into a single source of truth.

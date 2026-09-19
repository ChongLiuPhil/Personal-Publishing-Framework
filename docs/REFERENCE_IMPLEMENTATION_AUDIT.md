# PPF v0.1 Reference Implementation Audit

**Date:** 2026-09-19  
**Branch:** `reference-implementation-v0.1`  
**Status:** PASS — initial static audit + downstream runtime validation + current root-level template CI

> This file records the static audit of the initial reference-implementation branch. A real downstream runtime pilot has since been completed and fed improvements into the current `main` template; see `FIRST_PILOT_LESSONS.md`.

## Subject

`templates/quarto-book/`

This directory is the first PPF reference implementation, not the PPF specification itself.

## 1. Profile model

Confirmed:

- `_quarto.yml` default profile = `web`;
- Web output = `_book`;
- EPUB output = `_publication/epub`;
- PDF output = `_publication/pdf`;
- DOCX output = `_publication/docx`;
- LaTeX output = `_publication/latex`.

PASS.

## 2. Continuous vs on-demand

`publishing.yaml`:

- Web = `continuous`;
- EPUB/PDF/DOCX/LaTeX = `on-demand`.

`web.yml`:
- runs the shared `make web-publish-check` on PR/push;
- uses GitHub Actions only for independent Web validation;
- holds no Cloudflare deployment credential;
- performs no Cloudflare production deployment.

`cloudflare-contract-ci.yml`:
- pins Node / Wrangler;
- installs and verifies pinned Quarto on a clean runner;
- runs `make cloudflare-build`;
- simulates the Workers Builds environment without deploying.

`build-publication.yml`:
- manual `workflow_dispatch` only;
- explicitly selects EPUB/PDF/DOCX/LaTeX;
- uploads a GitHub Actions artifact;
- does not automatically release or externally publish.

PASS.

## 3. Cloudflare consistency

`wrangler.jsonc` uses:

`assets.directory = ./_book`

This matches the Quarto Web profile and workflow verification path.

PASS.

## 4. Publication intent vs provider implementation

- `publishing.yaml`: publication intent;
- `wrangler.jsonc`: Cloudflare provider-specific implementation.

The concerns remain separate.

PASS.

## 5. Source / artifact boundary

Example canonical source:
- QMD;
- BibTeX;
- metadata;
- original assets.

Derived directories:
- `_book/`
- `_publication/`

Derived directories are ignored by Git and do not replace canonical source.

PASS.

## 6. Workflow execution status

Historically, the template had only static audit coverage because its workflows lived under `templates/quarto-book/.github/workflows/`.

Since then:

1. the downstream `epistemology-textbook` pilot completed real runtime validation;
2. PPF added root-level `.github/workflows/reference-template-ci.yml`;
3. root CI enters `templates/quarto-book/`, installs the pinned Wrangler version, and runs:
   - `make check`
   - `make cloudflare-build`
4. the current reference template therefore has continuous upstream execution validation rather than relying only on static audit.

## Conclusion

**PASS.**

The PPF v0.1 Quarto reference implementation is merge-ready and ready for a real-project pilot.


## 7. Subsequent runtime pilot

The downstream runtime validation proposed by the initial audit was completed in `ChongLiuPhil/epistemology-textbook`.

Real runs validated:

- Web profile: PASS;
- rendered HTML integrity: PASS;
- EPUB / PDF / DOCX / LaTeX: all PASS;
- production-path GitHub Pages deployment: PASS.

The pilot also drove later revisions to the current template:

- continuous Web validation separated from provider-deployment activation;
- repository-owned `make web-publish-check` as the shared gate;
- Workers Builds + the GitHub App as the default Cloudflare Git-integration reference;
- `cloudflare-builds.yaml` as a PPF machine contract;
- pinned Node / Wrangler / Quarto exercised by contract CI;
- one-format-per-request artifact verification;
- separation of provider provisioning from recurring deployment credentials;
- Cloudflare MCP/OAuth as optional AI account automation rather than a PPF requirement.

See:

`docs/FIRST_PILOT_LESSONS.md`

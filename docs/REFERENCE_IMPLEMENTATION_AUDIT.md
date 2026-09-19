# PPF v0.1 Reference Implementation Audit

**Date:** 2026-09-19  
**Branch:** `reference-implementation-v0.1`  
**Status:** PASS — initial static reference-template audit

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
- builds Web on PR/push;
- verifies `_book/index.html`;
- deploys to Cloudflare only on main push.

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

There is no GitHub Actions run for this template in the PPF repository itself.

Reason: the workflows live under `templates/quarto-book/.github/workflows/`. They are **downstream project templates**, not root-level PPF repository workflows.

Therefore this audit establishes **static template validation**, not execution success inside PPF.

Runtime validation belongs in the first downstream pilot: `epistemology-textbook`.

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

- continuous Web build separated from provider-deployment activation;
- Cloudflare deployment staged by default;
- one-format-per-request artifact verification;
- separation of provider provisioning from recurring deployment credentials.

See:

`docs/FIRST_PILOT_LESSONS.md`

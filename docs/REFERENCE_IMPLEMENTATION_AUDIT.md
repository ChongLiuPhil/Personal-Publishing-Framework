# PPF v0.1 Reference Implementation Audit

**Date:** 2026-09-19  
**Branch:** `reference-implementation-v0.1`  
**Status:** PASS — initial static audit + downstream runtime validation + verified Cloudflare canonical production cutover + current root-level template CI

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

That sentence is the historical conclusion of the initial audit stage. The real downstream pilot has since been completed; the current reference implementation is no longer waiting for a pilot.


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


## 8. Upstream continuous template CI

The root-level PPF `Reference Template CI` has now executed successfully.

- first continuous-validation record: run `35428973528`;
- current-main reference validation: run `35444948817` @ `3e884e58db113a3ef5d499a6726784ea27fdd48f`, PASS;
- exact Wrangler installation/version check: PASS
- publication-contract validation: PASS
- clean-runner pinned Quarto installation + SHA-256 verification: PASS
- `make cloudflare-build`: PASS
- rendered Web-artifact validation: PASS

The current reference implementation therefore has all three forms of evidence:

1. initial static audit;
2. downstream real-project runtime evidence;
3. upstream continuous template execution validation.


## 9. Current Cloudflare staging/runtime evidence

The later real downstream pilot advanced the reference implementation from an executable repository contract to real provider staging/runtime verification.

Current durable evidence in `ChongLiuPhil/epistemology-textbook` records:

- Cloudflare account connection: VERIFIED;
- Cloudflare GitHub App / repository connection: VERIFIED;
- Worker target: VERIFIED;
- main Workers Build: PASS;
- non-production preview: PASS;
- main workers.dev HTTP/content runtime: PASS;
- preview workers.dev HTTP/content runtime: PASS;
- another Workers Build triggered after a later main push: PASS.

This evidence supports the reference implementation's separation of:

- repository intent from provider actual state;
- build success from runtime success;
- preview/runtime verification as a pre-cutover gate;
- provider action from repository write-back;
- provider production branch from canonical production.

Those staging/runtime results did not by themselves establish canonical cutover at that earlier stage. The project later completed the human security-profile decision, workers.dev canonical-identity migration, post-cutover runtime verification, and legacy Pages retirement.

Current publication state is now:

```text
Cloudflare workers.dev = current canonical production
GitHub Pages = legacy retired / owner-confirmed unpublished
Custom Domain = not applicable to this pilot
DNS migration = not required
```

## 10. Security-profile evidence boundary

The Cloudflare reference security profiles must be interpreted according to real pilot evidence:

- **Profile A — Workers Builds Native**: operationally verified; the managed user-token scope is broader than the routine needs of a pure static Worker and is not per-Worker least privilege;
- **Profile B — Hardened External CI**: **candidate / validate-only PASS**; repository/build validation passed in the candidate workflow, while credential, preview, and production deployment steps were not executed, so it is **not production-tested**;
- **Profile C — Future Native Granular**: the required combination is currently unavailable because of provider product capability.

Final production-security-profile selection remains a human-governed security decision. The first real pilot ultimately selected **Profile A — Workers Builds Native**. That pilot choice does not make Profile A mandatory for other PPF projects.

## 11. Current audit conclusion

The current reference implementation now has five layers of real evidence:

1. initial static audit;
2. downstream source/build/multi-format runtime validation;
3. downstream Cloudflare account/build/preview/workers.dev runtime validation;
4. downstream workers.dev canonical production cutover plus post-cutover verification;
5. upstream continuous Reference Template CI.

The first pilot completed:

- production security profile = Profile A;
- canonical production = workers.dev;
- post-cutover runtime verification = PASS;
- GitHub Pages legacy policy = RETIRE;
- repository-owner confirmation of `Unpublish site` on 2026-09-20.

Still unvalidated or not adopted by this pilot:

- Cloudflare Custom Domain / DNS migration — not required by this pilot;
- Profile B production deployment;
- Profile C native granular credential support;
- Amazon KDP / Kindle and external-publisher delivery.

The reference implementation can therefore be described as a **real-pilot-backed canonical-production reference**. This does not require every PPF project to use Cloudflare, workers.dev, or Profile A.

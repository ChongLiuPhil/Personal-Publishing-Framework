# PPF First Real Downstream Pilot: Lessons Fed Back Upstream

**Date:** 2026-09-19  
**Pilot:** `ChongLiuPhil/epistemology-textbook`  
**PPF base:** v0.1.0-draft @ `9326920e1920d18f0a71eac26d4068da9d6bdffe`

## 1. Purpose

The pilot tested whether one canonical Quarto source could actually support:

```text
QMD / BibTeX
    |
    +--> continuous Web
    |
    +--> explicit on-demand EPUB
    +--> explicit on-demand PDF
    +--> explicit on-demand DOCX
    +--> explicit on-demand LaTeX
```

while keeping BUILD, PUBLISH, and RELEASE distinct.

## 2. Runtime results

Real GitHub Actions runs validated:

- Governance: PASS
- Web profile render: PASS
- rendered HTML integrity: PASS
- EPUB: PASS
- DOCX: PASS
- LaTeX: PASS
- PDF: PASS
- GitHub Pages production deployment: PASS

PDF required project-specific CJK fonts plus TinyTeX and was materially heavier than EPUB, DOCX, or LaTeX. This supports keeping heavy publication formats on-demand rather than coupling them to the daily Web pipeline.

Observed runtimes are evidence from one runner environment, not a PPF performance specification.

## 3. Lesson one: continuous build and provider deployment should be separable

The initial reference template attempted Cloudflare deployment directly after a validated `main` push.

The real migration showed that a project can already have:

- canonical source;
- a Web profile;
- source/output validation;

while still lacking:

- provider account context;
- a Worker target;
- deployment credentials;
- a canonical URL;
- staging verification.

PPF therefore now makes explicit:

`continuous publication intent != unconditional provider deployment`

The reference template continuously builds and validates by default, while provider deployment requires explicit activation.

## 4. Lesson two: one on-demand request should build one format

Different formats introduce different toolchains.

PDF in particular may introduce:

- TeX;
- fonts;
- language-specific packages;
- print geometry.

The reference workflow should therefore let the user select one target format per explicit request and verify that the corresponding artifact actually exists.

This prevents one format's dependencies from becoming coupled to every publication build.

## 5. Lesson three: provider provisioning and recurring deployment should be separable

Cloudflare's current permission model illustrates the distinction:

- creating a Worker may require product-level Admin;
- deploying to an existing specific Worker only requires Editor for that Worker;
- changing a Custom Domain or Route additionally requires Workers Routes Write on the relevant zone.

A better long-lived model is therefore:

```text
one-time provisioning authority
        |
        +--> create/confirm resource
        +--> attach route/domain when needed

long-lived CI credential
        |
        +--> deploy only to the intended existing resource
```

PPF does not normatively define Cloudflare permissions, but its reference implementation should demonstrate least privilege and separate permission lifecycles.

## 6. Lesson four: publication migration must not overwrite existing project governance

The pilot's first CI failure was not a Quarto or PPF failure. The migration had accidentally removed a Working Memory invariant required by the downstream project's existing governance validator.

This demonstrates that:

- PPF governs publication lifecycle;
- existing collaboration, audit, licensing, or research governance must remain intact;
- a publication migration must not silently rewrite other governance layers.

This reinforces the architectural separation between PPF, AHICP, and portfolio/personal governance.

## 7. Lesson five: readiness state belongs in CI

If deployment readiness is machine-readable, changes to:

- provider state;
- canonical URL;
- deployment gates;
- readiness configuration;

should retrigger relevant validation.

Validating manuscript files while ignoring the publication contract or provider-readiness state leaves room for configuration drift.

## 8. Changes fed back into the v0.1 reference implementation

From this pilot:

1. continuous Web build is separated from Cloudflare deployment activation;
2. continuous Web validation is separated from provider-deployment activation;
3. repository-owned `make web-publish-check` becomes the canonical gate shared by GitHub Actions and Cloudflare;
4. Cloudflare Workers Builds + the GitHub App becomes the default reference delivery integration;
5. `cloudflare-builds.yaml` records intended Git connection / build / deploy / preview / readiness without pretending to be provider-account truth;
6. Node / Wrangler / Quarto are pinned in the reference implementation and exercised by non-deploying contract CI;
7. on-demand workflows verify the requested artifact;
8. the schema models deployment integration/readiness and release semantics;
9. documentation adds OAuth/MCP, GitHub App, provisioning, and recurring-deployment security boundaries;
10. root-level PPF CI continuously validates the reference template instead of relying only on one pilot.

## 9. Not yet validated by this pilot

This pilot did **not** validate:

- account-side Cloudflare deployment;
- Workers Custom Domain cutover;
- DNS migration;
- Amazon KDP / Kindle delivery;
- external-publisher DOCX workflows;
- formal release archive conventions.

Those remain later v0.1 pilot areas.


## 10. Subsequent Cloudflare ↔ GitHub reference validation

The same downstream pilot later validated the repository-side Cloudflare integration contract.

Real `epistemology-textbook` runs validated:

- GitHub Actions invoking the shared `make web-publish-check`: PASS;
- Node 24 pin: PASS;
- Wrangler 4.135.0 installation and version check: PASS;
- Quarto 1.10.18 downloaded on a clean runner with SHA-256 verification: PASS;
- `make cloudflare-build`: PASS;
- rendered Web-artifact validation: PASS;
- GitHub Pages production deployment after merge: PASS;
- no Cloudflare token / Wrangler deploy / Cloudflare deploy action in active GitHub workflows: PASS.

The reference implementation therefore now defaults to:

```text
GitHub Actions = independent validation
repository-owned gate = shared build/validation logic
Workers Builds = preferred Cloudflare Git delivery
Cloudflare MCP = optional agent-side account automation
GitHub Actions + scoped token = fallback
```

This stage still does **not** claim account-side Cloudflare deployment is complete. Worker/account/GitHub App connection, first Cloudflare preview, Custom Domain, and production cutover remain subject to later real account validation.

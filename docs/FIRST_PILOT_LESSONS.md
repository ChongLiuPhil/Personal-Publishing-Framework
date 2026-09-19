# PPF First Real Downstream Pilot: Lessons Fed Back Upstream

**Date:** 2026-09-19  
**Pilot:** `ChongLiuPhil/epistemology-textbook`  
**PPF base:** v0.1.0-draft @ `9326920e1920d18f0a71eac26d4068da9d6bdffe`  
**Current pilot evidence status:** Cloudflare staging/runtime VERIFIED; canonical production remains GitHub Pages; production cutover is not complete.

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

## 9. What remains unvalidated

The account-side pilot continued after the earlier repository-only phase. The following are now validated in a real project:

- Cloudflare GitHub App connection;
- Workers Builds main build;
- non-production preview build;
- main workers.dev runtime;
- preview workers.dev runtime;
- another automatic Workers Build after a later main push.

Still unvalidated:

- Workers Custom Domain cutover;
- DNS migration;
- final production security profile;
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

> **Historical stage note:** The statement above describes the earlier repository-side integration stage only. It was later **superseded** by the real account-side staging/runtime evidence in section 11. Current state must not be interpreted as account-side unverified.

At that stage, account-side Cloudflare deployment had not yet been claimed. Later real account validation established the GitHub App / repository connection, main build, preview, and workers.dev runtime; Custom Domain and canonical production cutover remain incomplete.


## 11. Cloudflare account-side staging and security profiles

The later real account-side pilot completed:

- Cloudflare GitHub App: PASS;
- repository connection: PASS;
- main Workers Build: PASS;
- non-production preview: PASS;
- main workers.dev HTTP/content verification: PASS;
- preview workers.dev HTTP/content verification: PASS;
- Cloudflare-managed build token: operationally verified.

The pilot also exposed an important product constraint:

- Workers Builds currently supports **user tokens** only;
- Cloudflare's newer granular Workers authorization supports **account-owned token + individual Worker + Editor**;
- therefore the native Workers Builds experience and true per-Worker least privilege cannot currently be fully combined.

PPF therefore defines three Cloudflare reference security profiles:

1. **Workers Builds Native** — current reference default with low manual setup and native Git integration, but a broader managed user-token scope;
2. **Hardened External CI** — a GitHub Actions + account-owned individual-Worker `Editor` hardened candidate; the current pilot reached repository/build **candidate / validate-only PASS** only, while credential / preview / production deployment steps were skipped in the PR context, so it must not be described as production-tested;
3. **Future Native Granular** — the ideal combination once Workers Builds supports account-owned tokens; it is currently recorded as unavailable rather than falsely supported.

See:

`docs/CLOUDFLARE_SECURITY_PROFILES.md`

The general PPF lesson is not Cloudflare-specific:

> when provider-native integration cannot simultaneously satisfy convenience and the required credential scope, the framework should record that trade-off explicitly and provide an auditable hardened alternative rather than silently describing broad permissions as least privilege.


## 12. Current reconciled pilot state

As of 2026-09-19, the durable pilot evidence should be read as:

- Cloudflare account connection: VERIFIED;
- GitHub App / repository connection: VERIFIED;
- main Workers Build: PASS;
- non-production preview: PASS;
- main workers.dev HTTP/content runtime: PASS;
- preview workers.dev HTTP/content runtime: PASS;
- Profile A — Workers Builds Native: operationally verified, but the managed user-token scope is broader than the routine needs of a pure static Worker and is not per-Worker least privilege;
- Profile B — Hardened External CI: candidate / validate-only PASS, **not production-tested**;
- Profile C — Future Native Granular: currently unavailable because of provider product capability;
- current canonical production: GitHub Pages;
- Cloudflare workers.dev: staging/runtime evidence, not canonical production;
- Custom Domain / canonical URL migration: NOT DONE;
- GitHub Pages legacy URL policy: UNRESOLVED;
- production security profile: WAITING HUMAN DECISION.

Therefore:

```text
provider build verified
+ preview/runtime verified
!= canonical production cutover
```

Cloudflare staging/runtime verification must not be reported as production cutover.

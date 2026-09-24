**Project links:** [Public homepage](https://inquirystack.philohub.workers.dev/ppf/) · [GitHub repository](https://github.com/ChongLiuPhil/Personal-Publishing-Framework)

**New to the full stack?** Start with the [AHICP homepage](https://inquirystack.philohub.workers.dev/), which explains the system from the user’s point of view and shows how to hand technical setup to an AI.

**Related public projects:** [AHICP homepage](https://inquirystack.philohub.workers.dev/) · [Vault Interface homepage](https://inquirystack.philohub.workers.dev/vault-interface/) · [Starter homepage](https://inquirystack.philohub.workers.dev/starter/)

**Ecosystem and agent entrypoint:** [`docs/ECOSYSTEM.md`](docs/ECOSYSTEM.md) · [`ecosystem.yaml`](ecosystem.yaml) · [`llms.txt`](docs/llms.txt) · [Starter unified guide](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/ECOSYSTEM.md) · [Agent retrieval contract](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/AGENT_RETRIEVAL_CONTRACT.md)

# Personal Publishing Framework

[English](README.md) | [中文](README.zh-CN.md)

**Personal Publishing Framework (PPF)** is a source-centered framework for keeping knowledge and creative work portable, rebuildable, and publishable over time.

> **Formats and platforms are replaceable; the source should endure.**

PPF is for anyone who wants to turn ideas, learning, writing, research, teaching materials, stories, poetry, or other creative work into durable publications that can evolve over time and be shared in more than one format.

It does not require professional scholarship, formal publishing, or AI. A project may be a child's poetry collection, a personal learning project, a technical guide, a public knowledge site, a long-running book, or a formal academic work.

## Core model

PPF separates the durable source of a work from its publication formats and delivery platforms.

```text
Creator-owned source
        |
        +---- Continuous publication ----> HTML / Web
        |
        +---- On-demand editions --------> EPUB
                                          PDF
                                          DOCX
                                          LaTeX
                                          Print
```

The durable source should remain portable and reconstructable even when publishing tools, hosting providers, or distribution platforms change.

For newly configured original or unpublished work, the reference safety default is a **private canonical source** with Continuous Web kept **restricted and authenticated** until explicit human public-release authorization. Public Web output never implies that the source repository must become public.

## Two publication modes

### Continuous publication

Some outputs, especially a Web edition, may be rebuilt automatically whenever accepted source material changes:

```text
source update
-> validate
-> build HTML
-> validate output
-> deployment readiness gate
-> deploy
-> verify
```

### Edition publication

Other formats are generated only when requested or when a release is intentionally frozen:

```text
source
-> build requested format
-> review
-> release
-> optional external publication
```

Examples include EPUB, PDF, DOCX, LaTeX, print-ready files, and platform-specific editions.

## Lifecycle

PPF models publishing as five related concerns:

1. **SOURCE** — durable, creator-controlled source material.
2. **BUILD** — transform source into one or more publication formats.
3. **PUBLISH** — make an output accessible to readers.
4. **RELEASE** — freeze a named or versioned edition when needed.
5. **ARCHIVE** — preserve enough source and release state to reconstruct the work later.

## Scope

PPF governs the publication lifecycle of human-created work. It does **not** define how humans and AI should collaborate.

Projects that use AI may adopt the **AI-Assisted Human Inquiry and Creation Protocol (AHICP)** as a compatible governance layer. PPF itself remains usable without AI.

## Reference implementation

The first reference implementation is expected to use:

- Git as the canonical versioned source
- Quarto / Pandoc for source-to-format transformation
- HTML as the default continuously published format
- GitHub Actions as an independent validation gate
- a repository-owned `make web-publish-check` as the canonical Web publication gate
- GitHub Actions + a project-scoped Cloudflare account-owned token as the preferred delivery path for **new agent-provisioned projects**; Workers Builds + the Cloudflare GitHub App remains the operational provider-native profile with real pilot evidence, and Cloudflare Pages remains supported for existing projects
- `project.infrastructure.json` as the machine-readable GitHub/Cloudflare desired-state manifest, with private-by-default visibility and a read-only reconciliation planner
- Cloudflare Workers Static Assets as a Web delivery layer
- EPUB, PDF, DOCX, and LaTeX as on-demand publication artifacts

These technologies are a reference stack, not requirements of the framework.

Quarto profiles are especially suitable for separating a default Web build from explicitly requested publication formats.

## Design principles

- **Source before format.**
- **Creator ownership before platform dependence.**
- **Continuous Web publication is distinct from formal editions.**
- **Build is distinct from release; release is distinct from external publication.**
- **Publication intent should be declarative and portable.**
- **A public repository does not automatically imply authorization to publish every output.**
- **The framework should remain useful for both short creative works and long-lived knowledge projects.**

## Planned specification

PPF v0.1 will define:

- a minimal project model;
- `publishing.yaml` as a declarative publication contract;
- continuous vs. on-demand publication modes;
- format-independent source expectations;
- release and archive semantics;
- reference workflows for Quarto, GitHub Actions, and Cloudflare;
- compatibility guidance for other tools and platforms.

## Reference implementation

The first executable reference implementation is available at [`templates/quarto-book/`](templates/quarto-book/README.md).

It implements the PPF model as:

```text
Git canonical source
-> repository-owned Web gate
-> GitHub Actions validation + authorized deployment
-> project-scoped Cloudflare Worker Editor credential
-> Cloudflare Workers Static Assets

explicit request
-> EPUB / PDF / DOCX / LaTeX
-> GitHub Actions artifact
```

The reference implementation is intentionally separate from the normative specification so that other toolchains can implement the same PPF lifecycle.

## Status

**Working version: v0.1.0-draft**

The project now includes the initial specification, an executable Quarto reference implementation, the first real downstream runtime pilot, the verified Workers Builds native path, and an implemented `agent-provisioned-external-ci` reference profile for future low-touch project creation. The external-CI profile still requires one clean end-to-end new-project pilot before it may be called production-accepted. PPF continuously validates the reference template with root-level CI. See `docs/FIRST_PILOT_LESSONS.md`, `docs/CLOUDFLARE_GITHUB_AUTHORIZATION.md`, and `docs/AGENT_PROVISIONED_EXTERNAL_CI.md`.


For the reusable GitHub–Cloudflare desired-state and reconciliation contract, see [`docs/GITHUB_CLOUDFLARE_INTEGRATION.md`](docs/GITHUB_CLOUDFLARE_INTEGRATION.md).

For Cloudflare reference-implementation production credential profiles, see:

`docs/CLOUDFLARE_SECURITY_PROFILES.md`

For the non-normative architecture research on generalizing the real Cloudflare pilot into a provider-integration pattern, see:

`docs/PROVIDER_INTEGRATION_PATTERN_RESEARCH.md`



## Composite Starter

For projects that need to compose AHICP with PPF and the public Vault Interface, or upgrade an existing GitHub project under explicit version pins, use:

https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter

The Starter handles composition, revision locking, project-provisioning intent, checks, and upgrade planning. PPF remains authoritative for the executable publishing and provider-infrastructure implementation.

## Licensing

This repository uses a **noncommercial split-license model** intended to support personal learning, education, research, public-benefit work, and other noncommercial reuse.

- Software, scripts, schemas, automation, machine-readable configuration, and executable templates: **PolyForm Noncommercial License 1.0.0**.
- Prose documentation, specifications, diagrams, educational content, and methodological materials: **CC BY-NC-SA 4.0**.
- Commercial use requires a separate commercial license.

See [LICENSE.md](LICENSE.md) and [COMMERCIAL-LICENSING.md](COMMERCIAL-LICENSING.md) for the authoritative repository-level licensing boundary.

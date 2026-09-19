# Personal Publishing Framework

[English](README.md) | [中文](README.zh-CN.md)

**Personal Publishing Framework (PPF)** is a source-centered, portable framework for developing, sharing, and publishing knowledge and creative work.

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

The canonical source should remain portable and reconstructable even when publishing tools, hosting providers, or distribution platforms change.

## Two publication modes

### Continuous publication

Some outputs, especially a Web edition, may be rebuilt automatically whenever accepted source material changes:

```text
source update
-> validate
-> build HTML
-> validate output
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
- GitHub Actions as a validation and publication gate
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

## Status

**Working version: v0.1.0-draft**

The project is in its initial specification and reference-implementation phase.

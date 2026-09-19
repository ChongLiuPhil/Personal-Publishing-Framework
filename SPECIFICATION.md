# Personal Publishing Framework — Specification

**Version:** v0.1.0-draft

## 1. Purpose

PPF defines a portable publication lifecycle for human-created work. It separates durable source material from generated formats, release decisions, and delivery infrastructure.

PPF is intentionally neutral about subject matter. A compliant project may contain knowledge work, educational material, research, essays, poetry, fiction, documentation, or other creative work.

## 2. Normative terms

- **MUST** — required for PPF conformance.
- **SHOULD** — recommended unless a project records a reason to differ.
- **MAY** — optional.

## 3. Core entities

### 3.1 Source

A PPF project MUST identify a canonical source.

The source SHOULD be:
- human-readable where practical;
- version-controlled;
- independent from any single publication format;
- sufficient, together with declared dependencies, to reconstruct supported outputs.

Generated HTML, PDF, EPUB, DOCX, LaTeX, or print files MUST NOT silently replace the canonical source.

### 3.2 Publication contract

A project SHOULD maintain a declarative publication contract, conventionally named `publishing.yaml`.

The contract records publication intent. Provider-specific configuration such as Cloudflare Wrangler settings is implementation state and SHOULD remain separate.

### 3.3 Publication modes

PPF defines two primary modes:

- **continuous** — rebuilt automatically from accepted source changes;
- **on-demand** — built only by explicit request or release workflow.

A project MAY define additional modes later, but their semantics MUST be explicit.

### 3.4 Artifact

A generated output is a publication artifact. Artifacts MAY include HTML, EPUB, PDF, DOCX, LaTeX, print files, or other representations.

Artifacts are derived unless a project explicitly declares otherwise.

### 3.5 Deployment readiness

`continuous` describes the publication intent that an output should be rebuilt as accepted source changes. It does **not** mean an external provider must be invoked unconditionally before that provider is configured.

When a deployment provider requires target resources, credentials, domains, or other prerequisites, a project MUST confirm those prerequisites before activating automatic deployment. Deployment activation SHOULD be explicit and auditable rather than inferred merely from the existence of a workflow file.

## 4. Lifecycle

PPF distinguishes:

```text
SOURCE -> BUILD -> PUBLISH -> RELEASE -> ARCHIVE
```

These are related actions, not synonyms.

### SOURCE
Maintain the durable work.

### BUILD
Transform source into an output format.

### PUBLISH
Make an output accessible.

### RELEASE
Freeze an intentional version or edition.

### ARCHIVE
Preserve enough source and release state for later reconstruction.

A build MUST NOT automatically be interpreted as a release. A release MUST NOT automatically authorize external publication unless the project declares that behavior.

## 5. Continuous Web publication

PPF RECOMMENDS HTML/Web as the default continuous publication mode when a project wants a continuously readable public edition.

A reference continuous pipeline is:

```text
accepted source change
-> source validation
-> HTML build
-> output validation
-> deployment readiness gate
-> deployment
-> production verification
```

A failed validation MUST stop publication.

While a deployment provider is not ready, continuous Web **build / validation** MAY remain active while provider deployment remains staged or disabled.

## 6. On-demand formats

Formats such as EPUB, PDF, DOCX, LaTeX, and print-ready files SHOULD default to on-demand generation unless the project has a documented reason to build them continuously.

Where practical, one explicit on-demand request SHOULD select and build one target format so that unrelated toolchains, fonts, TeX dependencies, or platform requirements do not become coupled to every publication build.

## 7. Portability

A PPF project SHOULD minimize format-specific markup in canonical content where doing so would unnecessarily prevent conversion to other supported formats.

Platform-specific enhancements MAY exist, but essential meaning SHOULD remain recoverable without them.

## 8. Authorization

Repository visibility and publication authorization are distinct concepts.

A public source repository MUST NOT by itself be interpreted as authorization to publish every possible output or distribution target.

## 9. AI neutrality

PPF does not require AI.

When AI assistance is used, a project MAY adopt a separate governance protocol such as the AI-Assisted Human Inquiry and Creation Protocol (AHICP).

PPF does not redefine authorship, agency, or responsibility.

## 10. Reference stack

The initial reference stack MAY use Git, Quarto/Pandoc, GitHub Actions, and Cloudflare Workers Static Assets. These implementations are not normative requirements.

Where a provider supports scoped permissions, the reference implementation SHOULD separate one-time infrastructure provisioning from long-lived recurring deployment credentials and use the least privilege sufficient for recurring deployment.

## 11. Versioning

The specification itself uses semantic versioning while under active development. Project editions MAY use another documented versioning scheme.

## 12. Conformance status

This draft now includes an initial schema, reference workflows, and feedback from the first real downstream runtime pilot. More complete conformance tests, release conventions, and provider-migration guides will continue to develop in later v0.1 revisions.

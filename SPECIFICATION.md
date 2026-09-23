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

A project MAY record source visibility such as `public`, `private`, or `restricted`. Source visibility describes who can see source material; it MUST NOT automatically determine publication authorization, publication visibility, or Web access policy.

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

When validation and deployment run in different CI/provider environments, a project SHOULD keep a repository-owned, provider-independent canonical build/validation gate so those environments invoke the same logic rather than copying validation rules that can drift.

A project MAY maintain a separate provider-integration machine contract describing intended repository connection, branch, build/deploy commands, and readiness. That contract MUST NOT be confused with real provider-account state. If the provider does not natively consume the contract, the project MUST say so explicitly.

### 3.6 Three classes of provider-integration state

PPF MUST distinguish at least three independent state classes:

1. **Repository Integration Intent** — the repository-declared desired integration, such as repository, branch, build/deploy commands, resource name, validation gate, and readiness intent;
2. **Provider Actual State** — the provider account's real current connection, resource, build, deployment, runtime, and credential/integration state;
3. **Human Authorization State** — identity authorization, account-owner consent, permission grants, production security profile, canonical/public cutover, and other states that require human authority or explicit confirmation.

These classes MUST NOT be collapsed merely because a file, workflow, or provider UI appears to be configured.

A provider's **production branch** is only a provider trigger / delivery configuration. A successful production-branch build or deployment **MUST NOT** automatically mean that:

- the canonical URL has changed;
- formal PPF production has moved;
- publication authorization is complete;
- the incumbent production can be retired.

### 3.7 Readiness vocabulary

PPF defines reusable provider-integration readiness labels:

~~~text
DECLARED
REPOSITORY_VALIDATED
ACCOUNT_CONNECTED
PROVIDER_BUILD_VERIFIED
PREVIEW_RUNTIME_VERIFIED
CUTOVER_READY
PRODUCTION_ACTIVE
~~~

These labels describe observable readiness milestones; they are **not a mandatory single linear state machine**. Provider-specific implementations MAY map, combine, validate in parallel, or add finer internal states, but they MUST preserve the semantic distinctions among the labels, especially the difference between build verification, staging/runtime verification, and canonical production activation.

### 3.8 Runtime verification

**Build success does not equal deployment/runtime success.**

Before a new provider is treated as cutover-ready, the project MUST perform real runtime verification appropriate to the artifact type. For Web publication, verification SHOULD cover, where applicable:

- the expected Git/source revision;
- HTTP success;
- representative pages;
- local CSS / JavaScript / images / fonts and other assets;
- primary navigation / TOC / internal links;
- content encoding and integrity of primary-language text;
- absence of unintended PDF / EPUB / DOCX / LaTeX or other publication artifacts;
- health of the incumbent production during provider migration until explicit cutover.

A reference implementation MAY use provider-specific probes, but the PPF normative core does not prescribe concrete URLs, commands, or UI.

### 3.9 Provider reconciliation, write-back, and production cutover

When an external provider action changes state that affects future publication work, the project SHOULD perform:

~~~text
repository intent
-> inspect provider actual state
-> act if authorized
-> verify runtime / provider result
-> write verified state back to repository
~~~

Repository durable state SHOULD record as needed:

- observed provider state;
- verification evidence or an evidence pointer;
- useful build / deployment identifiers;
- current blockers;
- current readiness / cutover state.

Secrets MUST NOT be stored in these records.

Production cutover **MUST** be an explicit gate. A project must at least be able to distinguish:

- provider build/deployment pipeline active;
- staging/runtime active and verified;
- canonical production active.

Until canonical/public cutover has explicitly completed, provider staging or a successful build MUST NOT be described as PRODUCTION_ACTIVE.

### 3.10 Legacy URL policy

If a public production URL already exists before migration, the project MUST record a legacy URL policy before retiring or replacing that URL.

General strategies may include:

- mirror;
- legacy-with-canonical;
- redirect;
- retire;
- or a documented provider-specific alternative.

Legacy URL policy is distinct from target-provider readiness. Successful runtime verification on the new provider does not automatically authorize shutting down the old site.

### 3.11 Publication visibility and access policy

PPF MUST distinguish:

- **Publication Authorization** — whether a particular artifact / channel is approved for publication;
- **Publication Visibility** — the intended visibility scope of an already published artifact;
- **Access Policy** — which visitors may actually enter the published artifact and what authentication / audience rule applies.

General publication-visibility semantics include at least:

- `public` — accessible to the public Internet;
- `restricted` — published, but available only to visitors satisfying an access policy;
- `private` — not generally available to an audience beyond the project-defined access boundary.

A project MAY use `authenticated`, `selected-audience`, or another documented access mode. Infrastructure access MUST use Cloudflare Access for Cloudflare-hosted Workers; application code MUST NOT add a second password, cookie, JWT, or session gate unless the project implements real application user accounts. Concrete identity providers, OTP, SSO, allowlists, and provider access-control products remain implementation details.

The following inferences are invalid:

~~~text
public source => public publication
private source => private publication
deployed runtime => public publication
publication authorized => unrestricted access
~~~

If publication visibility is `restricted` or `private`, a project SHOULD record the applicable access policy or explicitly record that the policy remains unresolved.

Passwords, tokens, private keys, recovery codes, and other secrets MUST NOT be stored in access-policy metadata.

### 3.12 Canonical publication identity and delivery provider

PPF MUST distinguish:

- **Provider URL / Endpoint** — the actual endpoint assigned or hosted by the current delivery provider;
- **Canonical Publication Identity** — the canonical URL identity that the project intends readers, citations, indexes, or other long-lived references to use.

Canonical identity MAY use a provider-native URL, a custom domain, or another explicitly documented naming form.

When long-term URL portability matters, a project **SHOULD** prefer a canonical identity that does not depend on one delivery provider. PPF does not require a project to purchase or configure a custom domain.

A successfully deployed provider-native endpoint does not automatically become the canonical identity. Establishing, migrating, or replacing canonical identity remains an explicit cutover / authorization decision.

During migration, a project MAY simultaneously have:

~~~text
provider endpoint
+ incumbent canonical URL
+ future canonical URL
~~~

The roles of these URLs MUST be recorded explicitly rather than inferred merely from which URL is currently reachable.

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
-> repository-owned validation/build gate
-> independent CI validation
-> provider readiness
-> provider build/deploy
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

## 8. Authorization, visibility, and access boundaries

A PPF project MUST model the following concepts separately and MUST NOT infer one automatically from another:

1. **Source / Repository Visibility** — who can see the source material or repository;
2. **Publication Authorization** — whether an artifact / channel is permitted to be published;
3. **Publication Visibility** — whether the published artifact is intended for a public, restricted, or private audience;
4. **Access Policy** — which visitors may actually enter and what authentication or audience rule applies;
5. **Canonical Publication Identity** — the URL identity intended for long-lived reader or citation use.

Therefore:

- a public source repository does not automatically authorize every output or distribution channel;
- a private source repository does not automatically require a private Web publication;
- publication authorization does not automatically mean unrestricted public access;
- a reachable provider runtime does not automatically make that endpoint the canonical URL;
- an access-controlled publication can still be a formal, authorized publication.

A project SHOULD record enough metadata in its publication contract to distinguish these states without turning provider product limitations into PPF core rules.

## 9. AI neutrality

PPF does not require AI.

When AI assistance is used, a project MAY adopt a separate governance protocol such as the AI-Assisted Human Inquiry and Creation Protocol (AHICP).

PPF does not redefine authorship, agency, or responsibility.

## 10. Reference stack

The initial reference stack MAY use Git, Quarto/Pandoc, GitHub Actions, Cloudflare Workers Builds, Wrangler, and Cloudflare Workers Static Assets. These implementations are not normative requirements.

Where provider-native Git integration is available, the reference implementation MAY use GitHub Actions for independent validation while the hosting provider's native build system owns delivery; both SHOULD invoke the same repository-owned publication gate.

If provider-native Git integration is unavailable, a project MAY use external CI such as GitHub Actions with a scoped deployment credential.

Where a provider supports scoped permissions, the reference implementation SHOULD separate one-time infrastructure provisioning from long-lived recurring deployment credentials and use the least privilege sufficient for recurring deployment.

If a provider-native integration cannot currently satisfy the credential scope required by the project, the project SHOULD record that trade-off explicitly rather than silently describing broader permissions as least privilege. A project MAY provide a hardened external-CI profile with a more narrowly scoped deployment credential until the provider-native integration can meet the same security requirement.

AI agents with MCP/OAuth support MAY assist with provider-side configuration. This is optional automation, not a PPF conformance requirement. The account owner retains control over identity authorization, permission scope, the production security profile, and production cutover.

## 11. Versioning and adoption pinning

The specification itself uses semantic versioning while under active development. Project editions MAY use another documented versioning scheme.

A downstream project adopting PPF SHOULD record:

- the upstream framework source;
- the adopted version/tag;
- an immutable adopted commit (or equivalent immutable revision);
- when relevant, the separately adopted reference-implementation/profile revision.

Later upstream PPF changes **MUST NOT** be silently treated as already adopted downstream. A new upstream revision becomes adopted project state only after the project explicitly updates its adoption metadata and completes the applicable validation.

## 12. Conformance status

This draft now includes an initial schema, reference workflows, and feedback from the first real downstream runtime pilot. More complete conformance tests, release conventions, and provider-migration guides will continue to develop in later v0.1 revisions.

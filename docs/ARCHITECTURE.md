# PPF Reference Architecture

PPF separates **publication intent** from **publication implementation**.

```text
Creator
  |
  v
Canonical source
  |
  +--> publishing.yaml  ---- declares intent
  |
  +--> build system     ---- implements transformations
          |
          +--> continuous Web artifact
          |       |
          |       +--> deployment-readiness gate
          |               |
          |               +--> deployment provider
          |
          +--> on-demand artifacts
                  |
                  +--> review / release / archive
```

## Normative layer

The PPF specification defines concepts such as:

- canonical source;
- publication artifacts;
- continuous and on-demand modes;
- build, publish, release, and archive separation;
- portability;
- publication authorization.

It does not require a specific AI assistant, Git provider, build engine, or hosting company.

## Reference implementation layer

The current reference implementation uses:

```text
GitHub repository
      |
      +--> QMD / Markdown / BibTeX / assets
      |
      +--> publishing.yaml
      +--> cloudflare-builds.yaml   (PPF machine contract)
      +--> wrangler.jsonc           (provider-native config)
      |
      +--> repository-owned Web gate
      |       make web-publish-check
      |              |
      |              +--> GitHub Actions validation
      |              |
      |              +--> Cloudflare Workers Builds
      |                        |
      |                        +--> preview: wrangler versions upload
      |                        +--> main:    wrangler deploy
      |
      +--> explicit request --> EPUB / PDF / DOCX / LaTeX
```

For a Quarto implementation, a Web profile may be the default while other formats are explicitly selected. Quarto supports profile-specific project configuration and a default profile.

For a Cloudflare implementation, the generated static directory can be declared as the Worker static-assets directory in Wrangler configuration.

The repository-owned Web gate is intentionally provider-independent. GitHub Actions can prove that accepted source renders correctly even when Cloudflare account access is absent, while Workers Builds can rerun the same gate before delivery.

`cloudflare-builds.yaml` is a PPF machine contract, not a Cloudflare-native configuration file. It declares the intended Git connection, commands, toolchain pins, and readiness state so an AI agent or human operator can configure Cloudflare consistently. The provider account remains the authority for actual provider-side state.

A reference implementation should distinguish **continuous Web build/validation** from **deployment activation**. A project may keep the continuous Web build healthy while a provider is still staged or unconfigured.

Provider provisioning should also be separated from recurring deployment where practical. When OAuth/MCP or a provider Git App is available, those interfaces may reduce manual secret handling, but they do not eliminate the need for explicit account-owner authorization and least-privilege review.

## Boundary with AHICP

PPF does not govern AI behavior, human approval of substantive claims, agent memory, or AI-to-human responsibility.

Those concerns belong to a separate governance layer such as the **AI-Assisted Human Inquiry and Creation Protocol (AHICP)**.

A project can therefore be:

```text
PPF only
```

or:

```text
AHICP + PPF
```

depending on whether AI-assisted inquiry or creation is part of the workflow.

## Boundary with personal governance

Portfolio-level decisions such as which projects are public, which are authorized for publication, and where they are deployed SHOULD live in a separate governance system rather than being duplicated into PPF itself.

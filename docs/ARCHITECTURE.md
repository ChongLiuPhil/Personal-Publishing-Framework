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
          |       +--> deployment provider
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

The initial reference implementation uses:

```text
GitHub repository
      |
      +--> QMD / Markdown / BibTeX / assets
      |
      +--> publishing.yaml
      |
      +--> Quarto profiles
      |
      +--> GitHub Actions
              |
              +--> HTML --> Cloudflare Workers Static Assets
              |
              +--> explicit request --> EPUB / PDF / DOCX / LaTeX
```

For a Quarto implementation, a Web profile may be the default while other formats are explicitly selected. Quarto supports profile-specific project configuration and a default profile.

For a Cloudflare implementation, the generated static directory can be declared as the Worker static-assets directory in Wrangler configuration.

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

# PPF Quarto Book Reference Template

This directory is the first executable reference implementation of the **Personal Publishing Framework (PPF)**.

It demonstrates one specific stack:

```text
QMD / Markdown / BibTeX
        |
      Quarto
        |
   +----+------------------+
   |                       |
   v                       v
HTML / Web            on-demand formats
   |                   EPUB / PDF
GitHub Actions         DOCX / LaTeX
   |
deployment-readiness gate
   |
Cloudflare Workers
Static Assets
```

The stack is illustrative, not normative. PPF itself does not require GitHub, Quarto, or Cloudflare.

## Default behavior

`_quarto.yml` declares `web` as the default profile.

Therefore:

```bash
quarto render
```

renders the Web edition only.

Explicit publication builds use:

```bash
quarto render --profile epub
quarto render --profile pdf
quarto render --profile docx
quarto render --profile latex
```

## Continuous Web publication

`.github/workflows/web.yml`:

- builds and validates the Web profile on pull requests and pushes to `main`;
- verifies that `_book/index.html` exists;
- keeps provider deployment staged by default;
- deploys a validated `main` push to Cloudflare only when `WEB_DEPLOY_ENABLED=true` and `PRODUCTION_URL` is configured;
- verifies the production URL after deployment.

Before enabling production deployment, first confirm that the Worker/deployment target is ready, then configure these GitHub repository secrets:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

Repository variables:

- `PRODUCTION_URL`
- `WEB_DEPLOY_ENABLED=true`

If `WEB_DEPLOY_ENABLED` is set to `true` while `PRODUCTION_URL` is empty, the workflow fails explicitly rather than entering a partially configured deployment state.

The Cloudflare API token should be scoped as narrowly as practical. For an existing Worker, a long-lived CI credential should normally be limited to deployment/edit access for that Worker. One-time provisioning permissions needed to create a Worker or change a Custom Domain/Route should not remain indefinitely in the normal content-publishing credential.

## On-demand formats

`.github/workflows/build-publication.yml` runs only through `workflow_dispatch`.

The user explicitly selects one of EPUB, PDF, DOCX, or LaTeX. The workflow verifies that an artifact with the expected extension actually exists before uploading it as a GitHub Actions artifact.

Formats such as PDF may require project-specific fonts, TeX packages, or other dependencies. Those belong in the downstream project's workflow rather than being imposed on every PPF project.

**Build is not Release, and Release is not external Publish.**

## Files to customize

Before using this template in a real project:

1. replace the book title and author in `_quarto.yml`;
2. replace `project.id`, title, and deployment values in `publishing.yaml`;
3. replace the Worker name in `wrangler.jsonc`;
4. complete provider staging/readiness before filling in the canonical production URL;
5. set `WEB_DEPLOY_ENABLED=true` only after the deployment target, secrets, and production URL are ready;
6. replace the sample QMD files;
7. add bibliography entries and original assets;
8. add project-specific validation before the deploy step where needed.

## Output directories

```text
_book/
  continuously built Web HTML

_publication/
  epub/
  pdf/
  docx/
  latex/
```

Generated directories are ignored by Git because they are derived artifacts.

## Publishing contract vs implementation config

`publishing.yaml` declares **publication intent**.

`wrangler.jsonc` declares one **Cloudflare implementation** of Web delivery.

Keeping those concerns separate allows another implementation to replace Cloudflare without redefining the PPF publication model.

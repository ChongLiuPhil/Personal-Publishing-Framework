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

- renders the Web profile on pull requests and on pushes to `main`;
- verifies that `_book/index.html` exists;
- deploys only validated `main` pushes to Cloudflare;
- optionally verifies the production URL.

Configure these GitHub repository secrets before enabling production deployment:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

Optionally set the repository variable:

- `PRODUCTION_URL`

The Cloudflare API token should be scoped as narrowly as practical for the target account/project.

## On-demand formats

`.github/workflows/build-publication.yml` runs only through `workflow_dispatch`.

The user explicitly selects one format:

- EPUB
- PDF
- DOCX
- LaTeX

The result is uploaded as a GitHub Actions artifact. Building an artifact does **not** mean releasing or externally publishing it.

## Files to customize

Before using this template in a real project:

1. replace the book title and author in `_quarto.yml`;
2. replace `project.id`, title, and deployment values in `publishing.yaml`;
3. replace the Worker name in `wrangler.jsonc`;
4. set the canonical production URL when known;
5. replace the sample QMD files;
6. add bibliography entries and original assets;
7. add project-specific validation before the deploy step where needed.

## Output directories

```text
_book/
  continuously published HTML

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

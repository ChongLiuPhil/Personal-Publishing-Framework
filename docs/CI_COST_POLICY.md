# Private Project CI Cost Policy

**Status:** canonical reference policy for private downstream projects  
**Profile:** `private-project-quota-saver`  
**Reviewed:** 2026-09-25

This policy exists because private GitHub-hosted Actions consume the repository owner's monthly Actions allowance, while standard GitHub-hosted runners in public repositories do not consume that private-repository allowance. Cloudflare Workers Builds has its own separate build-minute pool.

The policy optimizes ordinary private research/publishing projects for **minimal duplicate CI work**:

```text
Agent-side preflight
-> optional lightweight GitHub PR contract check
-> merge to main
-> Cloudflare Workers Builds
-> restricted deployment
```

GitHub Actions is not the default Web build/deploy provider for this profile.

## 1. Current provider economics

At the reviewed date:

- GitHub Free includes 2,000 GitHub Actions minutes per month for private repositories.
- Standard GitHub-hosted runners in public repositories are free.
- Cloudflare Workers Builds Free includes 3,000 build minutes per month.

Provider limits can change. Re-check current official billing/limits before making a paid-plan or quota-sensitive decision.

References:

- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://developers.cloudflare.com/workers/ci-cd/builds/limits-and-pricing/

## 2. Agent rule: do not debug through GitHub Actions

An Agent MUST NOT use repeated pushes and GitHub Actions runs as its iterative debugging loop.

Preferred sequence:

```text
EDIT
-> EDIT
-> EDIT
-> AGENT PREFLIGHT
-> COMPLETE DIFF REVIEW
-> ONE PR / PUSH
-> CI
```

If CI fails:

```text
read the complete failure
-> identify all related fixes
-> fix as one batch
-> rerun Agent-side preflight
-> retry once
```

Do not fix one failure, push, discover the next failure, and repeat.

## 3. Automatic GitHub Actions in private projects

The installable Quarto template has one automatic runner path:

`.github/workflows/project-check.yml`

It runs only for pull requests that change project/configuration infrastructure such as:

- `_quarto.yml`;
- `publishing.yaml`;
- `cloudflare-builds.yaml`;
- `ci-cost-policy.yaml`;
- `project.infrastructure.json`;
- Wrangler/package/toolchain files;
- Makefile/scripts;
- GitHub workflow files;
- template manifest.

Content-only changes such as manuscripts, chapters, references, notes, or ordinary prose do **not** start this workflow.

The light workflow:

- uses one Ubuntu job;
- has a 5-minute hard timeout;
- runs contract checks only;
- does not install Quarto, Chromium, Wrangler, Node dependencies, or TeX;
- uses workflow-level concurrency with `cancel-in-progress: true` so a newer PR revision supersedes an older in-progress light check.

## 4. No automatic GitHub Actions on main

For the default Native profile, a push to `main` does not trigger a GitHub Actions Web build or deployment.

Cloudflare Workers Builds owns the production Web build:

```text
main push
-> Cloudflare Workers Builds
-> bash scripts/cloudflare_build.sh
-> make web-publish-check
-> wrangler deploy
```

This avoids building the same Web artifact once in GitHub and again in Cloudflare.

## 5. Heavy workflows are manual

These workflows remain available but default to `workflow_dispatch`:

- `.github/workflows/web.yml` — full Web validation;
- `.github/workflows/cloudflare-contract-ci.yml` — locked Wrangler/Cloudflare contract validation;
- `.github/workflows/build-publication.yml` — explicit EPUB/PDF/DOCX/LaTeX artifact build;
- `.github/workflows/deploy-cloudflare.yml` — advanced External-CI deployment only.

Recommended reasons to run heavy validation:

- publishing-contract change;
- Cloudflare integration/config change;
- workflow/toolchain change;
- framework upgrade;
- public-release preparation;
- troubleshooting that cannot be resolved through Agent-side checks.

A routine manuscript/content edit is not sufficient reason.

## 6. Preview and non-production build policy

Cloudflare Workers Builds must keep:

```text
production branch: main
non-production branch builds: disabled
previews: disabled
```

until a project explicitly needs and accepts preview cost/access behavior.

This prevents Agent feature-branch pushes from consuming the separate Cloudflare build-minute pool.

## 7. Retry policy

For GitHub Actions:

- prefer re-running the failed job or failed workflow only;
- do not re-run successful heavy jobs merely because another job failed;
- cancel superseded light PR runs;
- avoid repeated retries without first changing the underlying state.

For Cloudflare Builds:

- do not make no-op pushes merely to retry;
- use provider retry/rebuild only after the failure cause is understood;
- one source change should normally correspond to one production build.

## 8. Artifact policy

Automatic workflows do not upload successful artifacts.

Manual publication artifact builds retain outputs for **3 days** by default.

Diagnostic artifacts, if added by a downstream project, SHOULD:

- upload only on failure;
- use the shortest practical retention, normally 1 day;
- exclude secrets and provider-private state.

## 9. When GitHub Actions quota is exhausted

If the private-repository Actions allowance is exhausted:

1. do not convert routine Agent iteration into repeated blocked workflow attempts;
2. continue Agent-side validation and repository work that does not require GitHub-hosted runners;
3. keep ordinary production Web deployment on Cloudflare Workers Builds;
4. defer optional/manual GitHub heavy validation until quota resets unless the user explicitly accepts paid usage;
5. do not automatically add a payment method, raise a budget, or change plan.

## 10. Public framework repositories

AHICP, PPF, Vault Interface, and Starter are public framework repositories. Their standard GitHub-hosted runner usage is currently free, so they may retain more exhaustive CI.

Do not copy that full framework CI footprint into private downstream projects.

The framework should test the reusable machinery; downstream private projects should consume the tested machinery with a thin validation layer.

## 11. Machine contract

The installable template records this policy in:

`ci-cost-policy.yaml`

and `project.infrastructure.json` records:

```json
"ciCostProfile": "private-project-quota-saver"
```

If a project intentionally wants exhaustive private-repository GitHub validation, it may select `full-validation` explicitly. That is a cost decision and should not be inferred by an Agent.

The advanced `agent-provisioned-external-ci` deployment path uses:

```text
ciCostProfile: external-ci-required
```

because GitHub Actions is part of that profile's deployment architecture.

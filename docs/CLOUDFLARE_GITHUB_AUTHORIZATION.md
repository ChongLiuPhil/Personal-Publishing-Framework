# Cloudflare ↔ GitHub One-Time Authorization Guide (PPF Reference)

This guide is for an operator with no technical background.

The goal is not to teach APIs, Wrangler, or CI. The human should complete only the account-owner authorization actions that cannot safely be delegated. After that, an AI agent or maintainer should continue from the repository's `cloudflare-builds.yaml`.

## 1. Recommended route

```text
AI Agent
   |
   +--> Cloudflare OAuth / MCP      (when the client supports it)

Cloudflare
   |
   +--> Workers Builds
            |
            +--> Cloudflare GitHub App
                    |
                    +--> selected repository only
```

Cloudflare API MCP:

`https://mcp.cloudflare.com/mcp`

Workers Builds MCP:

`https://builds.mcp.cloudflare.com/mcp`

`cloudflare-builds.yaml` is a **PPF machine contract**. Cloudflare does not automatically consume it; an AI agent or human operator applies its values to Workers Builds.

## 2. Authorize AI ↔ Cloudflare (optional but recommended)

If the AI client supports MCP:

1. Open Plugins / Connectors / MCP / Integrations.
2. Add the official Cloudflare MCP.
3. Sign in to Cloudflare.
4. If permission selection is available, keep only the permissions required for Workers / Workers Builds management.
5. Complete OAuth authorization.

Completion criterion:

> The AI agent can actually read Cloudflare account, Workers, or Workers Builds state.

If the client cannot expose Cloudflare MCP, PPF still works; use the Dashboard fallback.

## 3. Authorize Cloudflare ↔ GitHub

1. Open the Cloudflare Dashboard.
2. Go to **Workers & Pages**.
3. Choose **Create application → Import a repository**, or connect Git from the Builds settings of an existing Worker.
4. Select GitHub.
5. GitHub shows the Cloudflare Workers & Pages App authorization page.
6. If **All repositories** or **Only select repositories** is offered, choose **Only select repositories**.
7. Select only the repository required by the project.
8. Return to Cloudflare.

Completion criterion:

> Cloudflare can see the project repository without receiving access to unrelated repositories.

### After this one-time authorization

The human should stop doing routine build configuration manually. Current Cloudflare Workers Builds documentation exposes an API for repository connections, triggers, environment variables, build execution, and build monitoring after the GitHub App authorization exists.

For API automation, use a **user-scoped** token with:

~~~text
Workers Builds Configuration: Edit
Workers Scripts: Read
~~~

The first permission manages builds/triggers/configuration; the second is used to resolve the Worker's immutable tag. Keep this API token in the executing tool's secure secret store, not in Git or chat.

For Access application/policy automation, use a separate token with:

~~~text
Access: Apps and Policies Write
~~~

Add `Access: Organizations, Identity Providers, and Groups Write` only if the agent must create or modify the OTP/identity-provider configuration.

The canonical minimal-human execution contract lives in the Starter:
https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/CLOUDFLARE_MINIMAL_HUMAN_HANDOFF.md

## 4. The “Set up your application” page

The UI mapping below is a **dated observation from 2026-09-19**, not a permanent Cloudflare specification. See the full mapping and UI-drift rule in:

`docs/CLOUDFLARE_OBSERVED_UI_MAPPING.md`

The current Cloudflare creation flow may show the following fields.

### Project name

Use the Worker / project name.

Example:

`epistemology-textbook`

### Build command

Copy from `cloudflare-builds.yaml`.

PPF Quarto reference:

`bash scripts/cloudflare_build.sh`

Do not leave it blank for the reference template: the build installs pinned Quarto and invokes the canonical Web gate.

### Deploy command

Copy from the machine contract.

PPF reference:

`wrangler deploy`

### Builds for non-production branches

PPF reference recommendation:

**Enable it.**

This allows non-production branches to produce preview builds.

### Protect with Cloudflare Access

Do not decide this from repository public/private status.

Read the publication contract first:

~~~text
publication.web.authorization_state
publication.web.visibility
publication.web.access
~~~

Reference mapping:

- `visibility: public` + `access.mode: none`: normally remain public;
- `visibility: restricted`: enable Cloudflare Access according to the project's access policy;
- `visibility: private`: first define the private audience / route policy, then configure Access or keep the public route disabled/staged.

Current Cloudflare Workers documentation also supports configuring Access after creation for one Worker, production+preview, or a specific hostname/path. The creation-page checkbox is therefore not the sole source of access-policy truth.

See:

`docs/CLOUDFLARE_ACCESS_PROFILE.md`

for the provider mapping.

Do not put passwords, OTPs, tokens, or other secrets in `publishing.yaml` or chat.

### Advanced settings → Non-production branch deploy command

PPF reference:

`wrangler versions upload`

### Advanced settings → Path

For a project built from repository root:

`/`

Use the actual project directory for a monorepo.

### API token

Workers Builds can create/select a Cloudflare **user build token**.

Important:

- do not copy the token secret;
- do not commit it to Git;
- do not paste it into chat;
- do not store it in `cloudflare-builds.yaml`.

Workers Builds currently uses the user-token model. See:

`docs/CLOUDFLARE_SECURITY_PROFILES.md`

for the security trade-off.

### Variables

If the machine contract requires no variables:

**leave them empty.**

Do not invent variables or secrets merely to fill the form.

## 5. What if Production branch is not shown?

The creation page may not always display a separate production-branch field.

If it is absent:

1. do not block setup because of that field;
2. if the repository default branch is `main`, finish setup and inspect the resulting build/deployment record;
3. verify that the expected branch appears in Cloudflare's build record;
4. inspect the Worker's Builds trigger settings if further confirmation is needed.

Do not change unrelated settings merely to find a field that is not present.

## 6. What to verify after the first Deploy

Do not move directly to Custom Domain cutover.

First verify:

- Worker exists;
- GitHub repository connection works;
- main build passes;
- non-production preview passes;
- workers.dev / preview URL works;
- repository-defined build command actually runs;
- the previous production remains healthy during migration.

Only then proceed to Custom Domain / canonical URL / legacy-site policy.

## 7. Token security and production profile

The Workers Builds managed build-token path minimizes manual setup, but its default scope is broader than the routine deployment needs of a pure static Worker.

PPF defines three Cloudflare security profiles:

- **Profile A — Workers Builds Native**: native, low-manual-work reference default;
- **Profile B — Hardened External CI**: GitHub Actions + account-owned per-Worker Editor token;
- **Profile C — Future Native Granular**: ideal Workers Builds + account-owned per-Worker token combination once supported.

See:

`docs/CLOUDFLARE_SECURITY_PROFILES.md`

## 8. Do not do these before preview validation

- do not attach the final Custom Domain;
- do not change DNS;
- do not retire the old production site;
- do not change the canonical URL;
- do not treat preview as production cutover.

If the live Cloudflare UI differs from this guide, do not guess. Re-read the current provider UI, current official documentation, and repository machine contract; verify actual build/runtime state; then update the dated Observed UI Mapping / runbook with the new observation.

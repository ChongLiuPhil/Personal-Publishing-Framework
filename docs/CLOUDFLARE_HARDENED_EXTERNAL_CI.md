# Cloudflare Profile B: Hardened External CI

**PPF status:** optional hardened reference profile  
**Default:** automatic deployment is disabled

Profile B is for projects that explicitly require the routine deployment credential to be able to modify only one existing Worker.

## Architecture

```text
GitHub Actions
-> account-owned Cloudflare API token
-> one specified Worker
-> Editor
-> Wrangler
```

Cloudflare's current granular Workers permissions can scope an account-owned token to an individual Worker with the `Editor` role. For routine deployment to an existing Worker, this is narrower than the default user build-token scope used by Workers Builds.

## Template files

- `cloudflare-external-ci.yaml` — PPF machine contract
- `.github/workflows/cloudflare-external-ci.yml` — validate/manual deployment workflow

Pull requests run only:

`make cloudflare-build`

They do not read Cloudflare credentials and do not deploy.

Cloudflare credentials are read only when a human manually invokes `workflow_dispatch` with `preview` or `production`.

Production mode also requires the workflow ref to be `main`.

## Minimum human setup

Do this only after the project actually selects Profile B.

### Cloudflare

In **Manage Account → Account API Tokens**, create an account-owned token.

Target permissions:

- Scope: Specified Worker
- Worker: the project Worker
- Role: Editor

Do not add KV, R2, D1, all-zone Workers Routes, or Workers Admin merely for routine deployment.

### GitHub

In the repository:

**Settings → Secrets and variables → Actions**

Add:

Secret:

`CLOUDFLARE_API_TOKEN`

Variable:

`CLOUDFLARE_ACCOUNT_ID`

Never store the token secret in Git, chat, or the machine contract.

## Safe migration order

1. keep the currently verified deployment path;
2. merge the Profile B candidate;
3. pass candidate validate-only CI;
4. create the scoped token and GitHub secret/variable;
5. manually run preview;
6. verify preview;
7. manually run production;
8. verify production;
9. only then disable the old deployment trigger;
10. retire the old broad credential last.

Do not dismantle the working deployment path before validating the replacement.

## Relationship to Profile A

Profile A (Workers Builds Native) remains the low-manual-work reference default.

Profile B is not mandatory merely because it is more restrictive; it exists for projects that explicitly require per-Worker least privilege.

Re-evaluate Profile C if Workers Builds later supports account-owned per-Worker tokens.

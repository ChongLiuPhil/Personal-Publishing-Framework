# GitHub + Cloudflare Authorization Guide (PPF Reference)

**Reviewed:** 2026-09-24

PPF supports two deployment routes, but the default has changed.

## Default: per-project guided Workers Builds setup

For ordinary new projects under a personal GitHub account, use **Workers Builds Native** as the default.

The expected human involvement is small and project-scoped:

1. create or approve the private GitHub repository;
2. connect that repository to Cloudflare Workers Builds;
3. authorize the Cloudflare Git integration for that repository if GitHub asks;
4. protect the resulting Worker with Cloudflare Access, unless verified account-wide Access already covers it;
5. confirm the first restricted deployment.

After that bootstrap, pushes to the production branch should deploy automatically without repeating the GitHub/Cloudflare connection.

See [PER_PROJECT_GITHUB_CLOUDFLARE_SETUP.md](PER_PROJECT_GITHUB_CLOUDFLARE_SETUP.md).

## Why this is now the default

Cloudflare documents Workers Builds as the integrated CI/CD route for GitHub/GitLab users and specifically positions it as requiring minimal setup. It can connect a repository to a Worker and deploy automatically on push.

This route also has real pilot evidence in this repository.

It does **not** provide the same least-privilege credential model as the hardened external-CI profile. Workers Builds currently uses a provider-managed user-token model. That limitation is accepted for the default guided-project profile because the human explicitly authorizes the project connection.

## Personal GitHub repository default

The normal downstream project owner is a personal GitHub account.

Reference default:

```text
owner: ChongLiuPhil
ownerType: user
repositoryVisibility: private
```

A user may create the repository manually in GitHub before the Agent configures the project. The system does not require account-wide repository-creation automation.

If an authorized connector can create the private repository safely, it may do so, but that is an optimization rather than a prerequisite.

## Cloudflare Git authorization

For the native route, Cloudflare's Git integration is the deployment identity.

When connecting a repository for the first time, or when the Cloudflare GitHub App does not yet have access to the project repository, GitHub may require the user to authorize or expand repository access.

This is an accepted per-project human gate.

Prefer access limited to the intended repository where practical.

## Private Web access

The default project Web is restricted.

Preferred project-level setup:

```text
Workers & Pages
-> select Worker
-> Access
-> Protect this Worker behind Access
-> All traffic
-> approved authentication policy
```

If **Protect all Workers** is already enabled and verified on the account, the project may use that instead.

The infrastructure manifest can record either:

```text
worker-scoped-access
account-wide-access
```

Do not describe a Worker as private until anonymous access has actually been challenged or denied.

## What becomes automatic after project bootstrap

Once the repository connection and Access protection are verified, normal operation should be:

```text
source push to main
-> Workers Builds
-> project build
-> wrangler deploy
-> verify intended revision
```

A second test push must succeed without reconnecting GitHub or reauthorizing Cloudflare before the project is called operationally verified.

## Secrets

The native default does not require the user to paste a Cloudflare deployment token into GitHub Actions or chat.

Credentials remain provider-managed.

Never store provider credentials in Git, issues, PR descriptions, logs, or model context.

## Optional advanced profile: agent-provisioned external CI

The existing `agent-provisioned-external-ci` profile remains available for projects that require stronger deployment-credential isolation.

That profile uses:

- GitHub Actions;
- a project-scoped account-owned Cloudflare token;
- Trusted Secret Broker orchestration;
- an individual-Worker Editor scope.

It is an optional advanced profile, not the default onboarding route. Its Cloudflare granular-token issuer remains subject to live Provider acceptance.

See:

- [AGENT_PROVISIONED_EXTERNAL_CI.md](AGENT_PROVISIONED_EXTERNAL_CI.md)
- [TRUSTED_SECRET_BROKER.md](TRUSTED_SECRET_BROKER.md)

## Human-reserved gates

Regardless of profile, the following remain explicit human decisions:

- public Web publication;
- making the source repository public;
- expanding the reader audience;
- custom domain or DNS changes;
- permission-scope expansion;
- paid-plan or billing changes.

The practical goal is no longer “zero human interaction for every future project.” The practical goal is:

> **one short, documented project bootstrap; then ordinary pushes deploy automatically.**

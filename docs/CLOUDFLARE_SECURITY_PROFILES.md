# Cloudflare Deployment Security Profiles (PPF Reference)

**Reviewed:** 2026-09-24

This file describes only the Cloudflare PPF reference implementation. It is not a PPF conformance requirement.

## 1. Why security profiles are necessary

Current Cloudflare capabilities create a useful but real split:

- Workers Builds + the Cloudflare GitHub App is a low-manual-work provider-native integration with automatic Git-triggered builds;
- individual Workers can use granular roles such as `Editor`;
- individual-Worker granular authorization uses account-owned API tokens;
- Workers Builds still uses the user-token model for its build credential;
- therefore provider-native Workers Builds and one-Worker routine deployment credentials are still different security paths.

PPF records that distinction instead of presenting one path as universally optimal.

## 2. Profile A — Workers Builds Native

```text
GitHub
-> Cloudflare GitHub App
-> Workers Builds
-> provider-managed / selected user build token
-> wrangler deploy / versions upload
```

Best for projects that prioritize provider-native Git integration, automatic preview/production triggers, and keeping the deployment credential entirely on the Cloudflare side.

Advantages:

- native Git integration;
- simple preview and production triggers;
- build credential stays on the Cloudflare side;
- validated by the first real PPF pilot.

Current limitation:

- the native build token has broader scope than a pure static Worker's routine deployment needs;
- Workers Builds cannot currently consume an account-owned token restricted to one Worker.

PPF label:

`operational-native / real-pilot-verified / broader-than-ideal-token-scope`

## 3. Profile B — Agent-Provisioned External CI

```text
platform provisioner
-> create private GitHub repository
-> verify account-wide Access
-> create Cloudflare Worker
-> create account-owned token scoped to that Worker / Editor
-> trusted secret broker -> GitHub Actions secrets
-> GitHub Actions -> wrangler deploy
```

Profile id:

`agent-provisioned-external-ci`

This is the preferred **new-project automation profile** when the objective is minimal repeated human involvement plus one-Worker routine deployment authority.

Advantages:

- the platform provisioning principal is separated from the project deployment identity;
- the project deployment token is restricted to one existing Worker;
- routine deployment uses the Worker `Editor` role;
- no Cloudflare GitHub App authorization is required for each new repository;
- new projects can remain private/restricted by default behind an account-wide `all_workers` Access baseline;
- the secret broker can transfer the Cloudflare token into GitHub Actions without exposing plaintext to the model.

Costs and requirements:

- the platform must first have an authorized GitHub provisioning principal;
- the platform must have an authorized Cloudflare provisioning principal that can create Workers and account-owned tokens;
- account-wide Access protection must be verified before creating a project Worker;
- a trusted secret broker is required for the Cloudflare-token-to-GitHub-secret hop;
- preview automation is disabled by default until protected-preview acceptance.

PPF label:

`preferred-agent-provisioning / implemented-reference / live-new-project-acceptance-pending`

Current evidence boundary:

- schema, template, GitHub Actions workflow, provisioner state machine, reconciliation path, and tests are implemented;
- the existing repository has production evidence for Profile A, not yet for a clean Profile B project bootstrap;
- until one new-project end-to-end pilot succeeds, Profile B must not be described as production-accepted.

See [AGENT_PROVISIONED_EXTERNAL_CI.md](AGENT_PROVISIONED_EXTERNAL_CI.md).

## 4. Profile C — Future Native Granular

Ideal combination:

```text
Cloudflare GitHub App
-> Workers Builds
-> account-owned token
-> individual Worker
-> Editor
```

This would preserve native Workers Builds while providing one-Worker account-owned deployment credentials.

As of the reviewed date, Workers Builds still documents the user-token model for build credentials, so this combination is not yet the active reference path.

PPF label:

`future-native-granular / currently-unavailable-in-workers-builds`

## 5. Deployment credential security is separate from publication access

Profiles A / B / C answer:

> Which identity and permission scope may modify or deploy the Worker?

They do not answer:

> Which readers may access the deployed publication?

The latter belongs to PPF `publication.web.visibility` and `publication.web.access`.

Valid combinations therefore include:

```text
Profile A credential + public publication
Profile A credential + restricted publication
Profile B credential + public publication
Profile B credential + restricted publication
```

A deployment success never implies a public publication decision.

## 6. Platform authorization vs project authorization

PPF distinguishes:

### Platform authorization

Long-lived authority to provision infrastructure:

- GitHub provisioning principal;
- Cloudflare provisioning principal;
- trusted secret broker.

These should be authorized once within a bounded platform scope and reused for later projects.

### Project authorization

Durable project-level decisions:

- whether restricted deployment is allowed;
- whether the publication may become public;
- which audience may read it;
- whether a custom domain/canonical identity may be changed.

Public release, reader-audience expansion, domain/DNS authority expansion, and paid-plan changes remain human-reserved unless separately and explicitly pre-authorized.

## 7. Separate Custom Domain provisioning from routine deployment

For either Profile A or B, domain or route provisioning must not become permanent routine deployment authority.

Recommended:

```text
temporary / platform domain provisioning authority
-> attach and verify hostname

then

routine project deployment identity
-> one Worker Editor
-> no zone-route authority unless the deployment actually changes routing
```

## 8. PPF security principles

The Cloudflare reference implementation SHOULD:

1. record the selected security profile explicitly;
2. separate platform provisioning authority from routine project deployment authority;
3. not describe a provider-managed broad token as least privilege;
4. never store token values in Git, chat, public state, issues, PRs, or logs;
5. keep token plaintext out of model context through a trusted secret broker;
6. require verified account-wide protection before automatically creating a restricted project Worker;
7. keep public release independent from deployment success;
8. retain a provider-native profile for teams that prefer convenience over one-Worker token isolation;
9. re-evaluate these profiles when provider capabilities change.

## 9. Selection rule

For newly agent-provisioned projects, prefer **Profile B** after platform bootstrap.

Use **Profile A** when native Workers Builds is deliberately selected because provider-native Git integration is more important than one-Worker deployment-token isolation.

Use **Profile C** only after Workers Builds actually supports the required account-owned per-Worker token path and that path has been verified.

The first clean Profile B project must still pass live acceptance before the repository labels it production-accepted.

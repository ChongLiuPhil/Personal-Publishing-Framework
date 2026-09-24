# Cloudflare Deployment Security Profiles (PPF Reference)

**Reviewed:** 2026-09-24

This file describes only the Cloudflare PPF reference implementation. It is not a PPF conformance requirement.

## 1. Why security profiles are necessary

Current Cloudflare capabilities create a useful split:

- Workers Builds + the Cloudflare Git integration provides low-manual-work Git-triggered deployment;
- individual Workers can use granular roles such as `Editor`;
- individual-Worker granular authorization uses account-owned API tokens;
- Workers Builds still uses a provider-managed user-token model for its build credential;
- therefore the most convenient native Git path and the strongest one-Worker deployment credential isolation remain different profiles.

PPF records that trade-off explicitly.

## 2. Profile A — Workers Builds Native

```text
private GitHub repository
-> Cloudflare Git integration
-> Workers Builds
-> provider-managed user build credential
-> build / deploy automatically on main push
-> Worker-scoped Access by default
```

Profile id:

`workers-builds-native`

This is the **default profile for ordinary new projects**.

It is designed for one short, documented project bootstrap rather than account-wide zero-touch provisioning.

Advantages:

- native Git integration;
- automatic production build/deploy after repository connection;
- credential stays on the Cloudflare side;
- no Cloudflare deployment token needs to be copied into GitHub Actions or chat;
- verified by the existing real PPF pilot;
- compatible with Worker-scoped Access, so account-wide Access is optional.

Current limitation:

- the provider-managed native build credential has broader scope than a pure static Worker's routine deployment needs;
- Workers Builds cannot currently consume the account-owned one-Worker token used by Profile B.

PPF label:

`default-guided-project-setup / real-pilot-verified / broader-than-ideal-token-scope`

## 3. Profile B — Agent-Provisioned External CI

```text
platform provisioner
-> create/prepare private GitHub repository
-> create Cloudflare Worker
-> create account-owned token scoped to that Worker / Editor
-> trusted secret broker -> GitHub Actions secrets
-> GitHub Actions -> wrangler deploy
```

Profile id:

`agent-provisioned-external-ci`

This is an **optional advanced profile** for projects that prioritize one-Worker routine deployment authority and are willing to operate additional provisioning infrastructure.

Advantages:

- provisioning authority is separated from the project deployment identity;
- the project deployment token can be restricted to one existing Worker;
- routine deployment uses the Worker `Editor` role;
- the Trusted Secret Broker can transfer the Cloudflare token into GitHub Actions without exposing plaintext to the model.

Costs and requirements:

- an authorized GitHub provisioning/user identity is required if the system is expected to create repositories automatically;
- a Cloudflare provisioning identity must be able to create the Worker and mint the account-owned token;
- a trusted Secret Broker is required for the Cloudflare-token-to-GitHub-secret hop;
- the exact live Cloudflare granular-token issuer policy must be verified;
- preview automation stays disabled until protected-preview acceptance.

PPF label:

`optional-advanced / implemented-reference / live-provider-acceptance-pending`

Current evidence boundary:

- schema, optional GitHub Actions workflow, provisioner state machine, reconciliation path, atomic Secret Broker orchestration, and tests are implemented;
- the existing real production evidence belongs to Profile A;
- until a clean Profile B end-to-end Provider pilot succeeds, Profile B must not be described as production-accepted.

See [AGENT_PROVISIONED_EXTERNAL_CI.md](AGENT_PROVISIONED_EXTERNAL_CI.md).

## 4. Profile C — Future Native Granular

Ideal combination:

```text
Cloudflare Git integration
-> Workers Builds
-> account-owned token
-> individual Worker
-> Editor
```

This would preserve native Workers Builds convenience while adding one-Worker account-owned deployment credentials.

As of the reviewed date, Workers Builds still documents the provider-managed user-token model for build credentials, so this is not the active reference path.

PPF label:

`future-native-granular / currently-unavailable-in-workers-builds`

## 5. Deployment credential security is separate from publication access

Profiles A / B / C answer:

> Which identity and permission scope may modify or deploy the Worker?

They do not answer:

> Which readers may access the deployed publication?

Reader access belongs to PPF `publication.web.visibility` and `publication.web.access`.

Valid combinations include:

```text
Profile A credential + public publication
Profile A credential + restricted publication
Profile B credential + public publication
Profile B credential + restricted publication
```

A successful deployment never implies a public publication decision.

## 6. Project bootstrap vs optional platform authorization

The default Profile A uses **project bootstrap**:

- create or confirm the private personal-account repository;
- authorize the Cloudflare Git integration for that repository when required;
- protect the target Worker with Worker-scoped Access, or reuse already-verified account-wide Access;
- verify the first restricted deployment;
- verify a second push deploys without renewed authorization.

Profile B may instead use **platform authorization** when the operator deliberately wants reusable provisioning authority across projects.

The framework no longer requires platform-wide provisioning authorization merely to create an ordinary new project.

## 7. Separate Custom Domain provisioning from routine deployment

For either Profile A or B, domain/DNS authority is separate from ordinary source deployment.

Do not infer custom-domain permission from repository/Worker deployment permission.

## 8. PPF security principles

The Cloudflare reference implementation SHOULD:

1. record the selected security profile explicitly;
2. keep new source repositories private by default;
3. keep new unpublished Web output restricted/authenticated by default;
4. not describe a provider-managed broad token as least privilege;
5. never store credential values in Git, chat, public state, issues, PRs, or logs;
6. support Worker-scoped Access as the normal project default, while allowing verified account-wide Access;
7. keep preview deployments disabled until their access protection is verified;
8. keep public release independent from deployment success;
9. require a second push without renewed authorization before calling the native project connection operationally verified;
10. re-evaluate these profiles when provider capabilities change.

For Profile B specifically, token plaintext must remain outside model context through the Trusted Secret Broker.

## 9. Selection rule

For ordinary new projects under a personal GitHub account, use **Profile A — Workers Builds Native**.

Use **Profile B — Agent-Provisioned External CI** only when the project deliberately chooses stronger deployment-credential isolation and the required trusted infrastructure is available.

Use **Profile C** only after Workers Builds actually supports the required account-owned per-Worker token path and that path has been verified.

The practical default is therefore:

> **one short project bootstrap, then automatic deployment on ordinary pushes.**

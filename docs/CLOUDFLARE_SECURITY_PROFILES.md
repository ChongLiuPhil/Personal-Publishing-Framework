# Cloudflare Deployment Security Profiles (PPF Reference)

**Reviewed:** 2026-09-19

This file describes only the Cloudflare PPF reference implementation. It is not a PPF conformance requirement.

## 1. Why security profiles are necessary

The real pilot established that:

- Cloudflare Workers Builds + the GitHub App is a stable low-manual-work integration with native preview/production triggers;
- Cloudflare's current Workers permission model supports individual Worker + `Editor`;
- Workers Builds currently supports **user tokens** only;
- granular Wrangler authorization for individual Workers uses **account-owned API tokens**;
- therefore the native Workers Builds experience and true per-Worker least privilege cannot currently be combined completely.

The PPF reference implementation should make this trade-off explicit.

## 2. Profile A — Workers Builds Native

```text
GitHub
-> Cloudflare GitHub App
-> Workers Builds
-> Cloudflare-managed / selected user build token
-> wrangler deploy / versions upload
```

Best for projects that prioritize minimal setup, provider-native Git integration, automatic preview/production builds, and keeping Cloudflare deployment secrets out of GitHub.

Advantages:

- native Git integration;
- simple preview and production triggers;
- build token remains on the Cloudflare side;
- validated by the first real PPF pilot.

Current limitation:

- the automatically created build token is broader than a static Worker's routine deployment needs;
- Workers Builds cannot currently use the newer per-Worker account-owned `Editor` token model.

PPF label:

`reference-default / operational / broader-than-ideal-token-scope`

## 3. Profile B — Hardened External CI

```text
GitHub Actions
-> account-owned Cloudflare API token
-> individual Worker
-> Editor
-> wrangler deploy
```

Best for projects that require per-Worker least privilege and accept additional secret-management and CI setup.

Advantages:

- token can be restricted to one existing Worker;
- routine deployment needs only `Editor`;
- no KV / R2 / D1 permission is required merely to deploy;
- routine deployment does not need all-zone route write.

Costs:

- an account-owned token must be created;
- token + account ID must be stored in a CI secret store;
- preview/production trigger behavior must be implemented and validated by external CI;
- initial human setup is more involved.

PPF label:

`supported-hardened-alternative / pilot-candidate-validate-only`

Current real-pilot evidence boundary:

- candidate workflow repository/build validation: PASS;
- credential / preview / production deployment steps in the PR context: SKIPPED;
- account-owned per-Worker token: not configured;
- Profile B production deployment: not executed;
- therefore Profile B **must not** be described as production-tested.

## 4. Profile C — Future Native Granular

Ideal combination:

```text
Cloudflare GitHub App
-> Workers Builds
-> account-owned token
-> individual Worker
-> Editor
```

This would preserve Workers Builds native Git behavior while providing per-Worker least privilege.

As of the reviewed date, Cloudflare Workers Builds documentation still states that only user tokens are supported and account-owned token support is not yet available.

PPF label:

`future-preferred / currently-unavailable`

## 5. Separate deployment-credential security from publication access

Profiles A / B / C answer:

> “Which identity and permission scope can modify / deploy the Worker?”

They do not answer:

> “Which readers may access the publication after deployment?”

The latter belongs to PPF `publication.web.visibility` and `publication.web.access`, which the Cloudflare reference can map to Cloudflare Access.

All of these combinations may therefore be valid:

~~~text
Profile A deployment credential + public publication
Profile A deployment credential + restricted publication
Profile B deployment credential + public publication
Profile B deployment credential + restricted publication
~~~

Deployment-credential least privilege and reader access control are orthogonal security axes.

See:

`docs/CLOUDFLARE_ACCESS_PROFILE.md`

for reader-access mapping.

## 6. Separate Custom Domain provisioning from routine deployment

For either Profile A or B, route/domain provisioning should not become permanent routine-deployment authority.

Recommended:

```text
temporary domain provisioning authority
-> Worker access
-> affected zone Workers Routes Write
-> attach/verify domain

then

routine deployment identity
-> no zone-route write unless a deployment actually changes routing
```

## 7. PPF security principles

The Cloudflare reference implementation SHOULD:

1. record the selected security profile explicitly;
2. not describe a provider-managed broad token as least privilege;
3. never store token secrets in Git, chat, or the machine contract;
4. not break an already verified pipeline merely to pursue theoretical hardening without a rollback path;
5. provide an external-CI hardened alternative when provider-native integration cannot satisfy the required credential scope;
6. re-evaluate the profile when provider capabilities change.

## 8. Selection rule

Profile A is the reference convenience default, not a claim that it is optimal for every security environment.

If a project requires before production that:

> the routine deployment credential can modify only one existing Worker

then Profile B should be selected until Profile C becomes supported by Workers Builds.

The project owner should confirm the production security profile.

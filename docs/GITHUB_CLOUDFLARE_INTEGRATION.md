# GitHub–Cloudflare Infrastructure Integration

**Reviewed:** 2026-09-24

PPF projects declare hosting intent in `project.infrastructure.json`. The manifest is desired state; GitHub and Cloudflare API responses plus HTTP probes are actual state. Provider adapters read actual state first, the planner emits the smallest idempotent reconciliation plan, and an orchestrator may apply only operations whose authorization and publication gates have passed.

For new-project automation, also read [AGENT_PROVISIONED_EXTERNAL_CI.md](AGENT_PROVISIONED_EXTERNAL_CI.md). For browser-agent work, read [WEB_AGENT_GITHUB_CLOUDFLARE_ONBOARDING.md](WEB_AGENT_GITHUB_CLOUDFLARE_ONBOARDING.md).

## Visibility and safe defaults

Repository and application visibility are independent.

New projects default to:

- private GitHub repository;
- private/restricted Worker behind account-wide Access;
- no public bypass;
- previews disabled until protected-preview verification;
- no custom domain;
- no paid services;
- explicit human authorization before public release.

`release.state: public` is intended state, not approval. Public repository and public website transitions use separate gates.

## Per-project guided bootstrap vs advanced platform provisioning

The default operational model is now **per-project guided bootstrap**.

For an ordinary new project under a personal GitHub account:

1. create or confirm the private repository;
2. connect it to Cloudflare Workers Builds through the native Git integration;
3. authorize that repository when GitHub/Cloudflare asks;
4. protect the resulting Worker with Worker-scoped Cloudflare Access, or reuse an already-verified account-wide Access policy;
5. verify the first deployment and one subsequent push.

This path deliberately allows a short human setup once per project. It does not require a platform-wide Project Provisioner, Trusted Secret Broker, or account-owned deployment token.

The advanced `agent-provisioned-external-ci` profile still separates long-lived platform authority from project deployment authority. Its existing provisioner, Secret Broker contract, and scoped-token design remain available when a project explicitly selects that profile.

Public release remains outside both default project bootstrap and advanced standing authorization.

See `docs/PER_PROJECT_GITHUB_CLOUDFLARE_SETUP.md` for the operator flow.

## Files and commands

- `schema/project.infrastructure.schema.json` defines desired infrastructure state.
- `templates/quarto-book/project.infrastructure.json` is the private-by-default v2 example.
- `schema/integration-state.schema.json` defines non-secret provider state.
- `providers/infrastructure/manifest.py` validates desired state and security-profile invariants.
- `providers/infrastructure/plan.py` creates a read-only reconciliation plan.
- `providers/infrastructure/provisioning.py` implements the new-project `plan / apply / verify-restricted` state machine.
- `providers/infrastructure/github.py` reads/creates repositories and reads only Actions-secret metadata.
- `providers/infrastructure/cloudflare.py` reads/creates Worker metadata, Workers Builds state, and Access state.
- `providers/infrastructure/coordinator.py` provides `doctor / plan / apply / verify / rollback` reconciliation after provisioning.
- `providers/infrastructure/state.py` stores only non-secret IDs/audit events in a protected state directory when this CLI implementation is used.

Examples:

```sh
python providers/infrastructure/manifest.py project.infrastructure.json
python -m providers.infrastructure.provisioning plan project.infrastructure.json
python -m providers.infrastructure.provisioning apply project.infrastructure.json
python -m providers.infrastructure.provisioning verify-restricted project.infrastructure.json --url https://example.workers.dev

python -m providers.infrastructure.coordinator doctor project.infrastructure.json
python -m providers.infrastructure.coordinator plan project.infrastructure.json
python -m providers.infrastructure.coordinator apply project.infrastructure.json
python -m providers.infrastructure.coordinator verify project.infrastructure.json
python -m providers.infrastructure.coordinator rollback project.infrastructure.json
```

## Credential boundary

Provider credentials are supplied only through protected execution environments or provider connections. They are never accepted as repository data.

For `agent-provisioned-external-ci`, the provisioner intentionally does **not** create or return the project token. It returns a non-secret `ppf/secret-broker-request/v1`.

The trusted broker performs:

```text
create account-owned Cloudflare token
-> scope to individual Worker / Editor
-> encrypt/write GitHub Actions secret
-> discard plaintext
```

The language model receives only status and non-secret identifiers.

The GitHub adapter may list secret **names** to determine readiness. It never reads secret values.

## Provider behavior

### Cloudflare Access

A private project may use either of two verified Access modes:

- `worker-scoped-access` — the default guided setup; protect the target Worker itself.
- `account-wide-access` — optional; protect all existing and future Workers.

The coordinator and reconciliation planner record which mode is intended. A project must not claim private readiness until the corresponding protection is observed and anonymous access is challenged or denied.

For the worker-scoped default, if the Worker exists but Worker-level Access is missing, reconciliation reports a project-level Access gate rather than requiring account bootstrap.

### Agent-provisioned external CI

The platform Cloudflare principal may use Workers product-level Admin to create Worker metadata. Routine deployment then moves to an account-owned token scoped to the individual Worker with `Editor`.

The installable template deploys through GitHub Actions with `wrangler deploy`.

### Workers Builds Native

Workers Builds Native is the **default profile for ordinary new projects**. It connects the project repository directly to Cloudflare and deploys automatically on push after the one-time project connection.

Workers Builds uses immutable Worker tags, repository connections, triggers, and a provider-managed user-token build credential. Those identifiers remain separate from Worker names and secret values.

Do not describe the Workers Builds build credential as one-Worker least privilege. The trade-off is accepted for the default guided route because the user explicitly authorizes the project connection.

### Agent-provisioned external CI

The platform Cloudflare principal may use Workers product-level Admin to create Worker metadata. Routine deployment then moves to an account-owned token scoped to the individual Worker with `Editor`.

The installable template retains a GitHub Actions deployment workflow for this optional advanced profile. It is not the default onboarding route.

## Human gates

The default route intentionally permits a small human bootstrap once per project.

Return to the human when needed to:

- create/confirm the private personal-account repository;
- authorize the Cloudflare Git integration for that repository;
- enable Worker-scoped Access or select an approved Access policy;
- confirm the first restricted deployment.

After that project bootstrap, ordinary pushes should not require renewed GitHub/Cloudflare authorization.

Always return to the human for:

- public publication;
- source-repository public/open-source transition;
- reader-audience expansion;
- custom-domain/DNS authority;
- provider-permission scope expansion;
- paid-plan or billing changes;
- direct secret input if an advanced profile cannot complete its trusted secret transfer.

## Verification

Default guided-project deployment is complete only when:

- desired and actual repository/Worker identities match;
- the repository remains private;
- the Cloudflare Git repository connection points to the intended repository;
- the production branch is correct;
- Worker-scoped Access (or verified account-wide Access) protects the project;
- the expected revision is deployed;
- anonymous production access is denied/challenged;
- enabled previews are also denied/challenged anonymously;
- direct assets do not bypass access control;
- a second source push triggers a new deployment without reauthorization;
- rollback/restore evidence is recorded;
- no credential value appears in Git, logs, PRs, issues, or chat.

Repository CI and simulation do not substitute for live project verification.

## Current implementation boundary

The verified Workers Builds Native route is now the default onboarding profile because it has real pilot evidence and Cloudflare's integrated Git workflow minimizes per-project setup.

The infrastructure schema now represents both Worker-scoped and account-wide Access. The reference template defaults to `workers-builds-native`, private source, Worker-scoped Access, and previews disabled until explicitly enabled and protected.

The external-CI implementation remains available in the schema, optional GitHub Actions workflow, provider adapters, provisioner, reconciliation planner, atomic Secret Broker orchestration, safe broker result schema, and tests. Its Provider-specific Cloudflare granular-token issuer remains live-acceptance-pending.



Current provider references were rechecked on 2026-09-24:

- Cloudflare Workers authorization/roles: <https://developers.cloudflare.com/workers/platform/authorization/>
- Cloudflare Workers Access: <https://developers.cloudflare.com/workers/configuration/cloudflare-access/>
- Cloudflare Workers Builds API: <https://developers.cloudflare.com/workers/ci-cd/builds/api-reference/>
- Cloudflare GitHub Actions deployment: <https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/>
- GitHub repository API: <https://docs.github.com/en/rest/repos/repos>
- GitHub Actions secrets API: <https://docs.github.com/en/rest/actions/secrets>

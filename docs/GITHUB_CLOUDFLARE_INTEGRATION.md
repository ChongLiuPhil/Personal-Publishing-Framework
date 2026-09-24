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

## Platform bootstrap vs project provisioning

The preferred low-touch model separates long-lived platform authority from project deployment authority.

### Platform bootstrap

Authorize once within a bounded scope:

- a GitHub provisioning principal;
- a Cloudflare provisioning principal;
- a trusted secret broker;
- an account-wide Cloudflare Access baseline covering `all_workers`.

The project workflow must not create or disable the account-wide Access baseline.

### Project provisioning

For each new project, the provisioner may:

1. create the private repository;
2. create Worker metadata after verifying account-wide Access;
3. request a project-scoped Cloudflare token;
4. have the trusted broker write deployment credentials to GitHub Actions secrets;
5. let repository CI perform the authorized deployment;
6. verify restricted runtime behavior and revision;
7. write back only non-secret provider state.

Public release remains outside this standing project-creation authority.

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

An account-level `all_workers` destination can protect existing and future Workers. Project provisioning fails closed when this baseline cannot be verified.

A public production hostname becomes an explicit exception, not a replacement for the baseline. Previews remain protected unless separately approved.

### Agent-provisioned external CI

The platform Cloudflare principal may use Workers product-level Admin to create Worker metadata. Routine deployment then moves to an account-owned token scoped to the individual Worker with `Editor`.

The installable template deploys through GitHub Actions with `wrangler deploy`.

### Workers Builds Native

The provider-native profile remains supported. Workers Builds uses immutable Worker tags, repository connections, triggers, and a user-token build credential. Those identifiers remain separate from Worker names and secret values.

Do not describe the Workers Builds build credential as one-Worker least privilege.

## Human gates

After platform bootstrap, ordinary creation of another project inside the already approved scope should not require repeated account-level authorization.

Return to the human for:

- new GitHub organization/App installation scope;
- new Cloudflare permission scope;
- missing account-wide Access baseline;
- public publication;
- reader-audience expansion;
- custom-domain/DNS authority;
- paid-plan changes;
- direct secret input if the trusted broker cannot complete the secret transfer.

## Verification

Restricted deployment is complete only when:

- desired and actual repository/Worker identities match;
- repository remains private;
- account-wide Access remains enabled;
- GitHub Actions deployment secrets are installed as metadata, without reading their values;
- the expected revision is deployed;
- anonymous production access is denied/challenged;
- enabled previews are also denied/challenged anonymously;
- direct assets do not bypass access control;
- rollback is recorded;
- no credential value appears in Git, logs, PRs, issues, or chat.

Simulation and repository CI do not count as a live new-project acceptance.

## Current implementation boundary

The external-CI implementation is now present in the schema, Quarto template, GitHub Actions workflow, provider adapters, provisioner, reconciliation planner, and tests.

The existing real pilot proves the Workers Builds Native route. The new external-CI route still requires one clean end-to-end project pilot before it may be marked production-accepted.

Current provider references were rechecked on 2026-09-24:

- Cloudflare Workers authorization/roles: <https://developers.cloudflare.com/workers/platform/authorization/>
- Cloudflare Workers Access: <https://developers.cloudflare.com/workers/configuration/cloudflare-access/>
- Cloudflare Workers Builds API: <https://developers.cloudflare.com/workers/ci-cd/builds/api-reference/>
- Cloudflare GitHub Actions deployment: <https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/>
- GitHub repository API: <https://docs.github.com/en/rest/repos/repos>
- GitHub Actions secrets API: <https://docs.github.com/en/rest/actions/secrets>

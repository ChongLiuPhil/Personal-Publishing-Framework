# Agent-provisioned external CI profile

**Status:** implemented reference profile; live new-project acceptance pending  
**Profile id:** `agent-provisioned-external-ci`

This profile is an optional advanced path when a project specifically prioritizes minimal repeated human involvement and one-Worker deployment credentials over the simpler per-project Workers Builds setup.

It complements, rather than deletes, the provider-native Workers Builds profile.

## 1. Target experience

When this advanced profile has completed its platform bootstrap, a human should be able to give an agent a project request and let the agent perform the routine infrastructure work:

```text
project request
-> private GitHub repository
-> stack/template adoption
-> account-wide Access precondition
-> Cloudflare Worker metadata
-> project-scoped deployment credential
-> GitHub Actions deployment
-> restricted runtime verification
-> durable non-secret write-back
```

The human returns only for decisions that remain human-reserved: public release, a new reader audience, a new canonical domain or DNS authority, a paid-plan change, or a provider permission expansion.

## 2. Two platform-level authorizations

The desired steady state uses two long-lived trust relationships.

### GitHub provisioning principal

Use a clearly bounded GitHub account/organization scope. The provisioning GitHub App should request only the capabilities needed for project creation and maintenance. Depending on the exact implementation these normally include repository Administration write, Contents write, Workflows write, Actions write, Secrets write, Pull requests write, and Metadata read.

Repository creation differs by owner type:
- for a **personal user account**, GitHub's authenticated-user repository-creation endpoint accepts a GitHub App **user access token** (or another supported user-authorized fine-grained token), not an installation token;
- for an **organization**, the organization repository-creation endpoint accepts GitHub App installation access tokens as well as user access tokens.

The manifest therefore records `github.ownerType`. The platform provisioning principal must match that owner type.

The App/user authorization is platform authorization. A new project must not ask the human to reauthorize merely because another repository is created within the already approved scope.

### Cloudflare provisioning principal

Create one narrowly controlled platform credential or OAuth/MCP authorization that can inspect the account, verify the account-wide Access baseline, create a Worker, read deployment/observability state, and perform only separately authorized Access changes.

**Token minting is a separate high-privilege boundary.** Cloudflare's account-owned token API currently requires Super Administrator authority for creating/updating account-owned tokens. Do not put that authority in the ordinary project Agent or CI credential. Isolate it inside the trusted Secret Broker / provisioning service.

Creating new Workers requires product-level Workers Admin. Routine project deployments do not.

## 3. Private-by-default Cloudflare baseline

Before the provisioner creates any project Worker, Cloudflare Access must already protect all Workers in the account through an `all_workers` destination or an equivalent verified account-wide baseline.

This baseline covers existing and future Workers. The provisioner must fail closed if it cannot verify that protection.

A public project is implemented as an explicit, reviewed exception to the baseline. Public production never implies public previews.

## 4. Worker creation and deployment identities

Cloudflare now distinguishes Workers product-wide and individual-Worker scopes.

The platform provisioning principal may use product-level Admin to create a Worker. After the Worker exists, the routine deployment credential should be an **account-owned API token scoped to that individual Worker with the Editor role**.

That project token may update and deploy the Worker but must not be treated as authority over unrelated Workers.

The template therefore declares:

```yaml
deployment:
  provider: github-actions-cloudflare-workers
  securityProfile: agent-provisioned-external-ci
  credentialStrategy: project-scoped-account-token
  secretBroker: true
```

## 5. Secret broker boundary

A project-scoped token must never be returned to the language model, printed to logs, committed to Git, or stored in public project state.

The provisioner emits only a non-secret request:

```json
{
  "schema": "ppf/secret-broker-request/v1",
  "credential": {
    "scope": "individual-worker",
    "role": "Editor"
  },
  "target": {
    "provider": "github-actions",
    "secretNames": [
      "CLOUDFLARE_API_TOKEN",
      "CLOUDFLARE_ACCOUNT_ID"
    ]
  }
}
```

A trusted tool or service with the isolated token-minting authority executes the atomic secret path:

```text
Cloudflare token creation
-> plaintext exists only inside the trusted broker
-> encrypt/write GitHub Actions secret
-> discard plaintext
```

The model receives only installation status and non-secret identifiers.

The reference broker orchestration is now executable in `providers/infrastructure/secret_broker.py`. It refuses to overwrite existing target Secrets, verifies the minted scope returned by its issuer adapter, rolls back Secrets written during the current transaction when a later write fails, revokes the newly minted token on rollback, best-effort wipes the mutable token buffer, and returns only `ppf/secret-broker-result/v1`. See [`TRUSTED_SECRET_BROKER.md`](TRUSTED_SECRET_BROKER.md).

The Cloudflare granular-token **issuer adapter** remains a separate live-acceptance item. PPF deliberately does not hard-code a guessed “Specified Workers + Editor” policy-resource JSON representation; the first authorized pilot must discover and verify the current provider shape before that adapter is frozen.

## 6. Repository deployment workflow

The reference template contains `.github/workflows/deploy-cloudflare.yml`.

It:

1. runs only on `main` or manual dispatch;
2. reads the durable PPF publication contract;
3. does nothing while Web deployment remains unauthorized or disabled;
4. builds through the repository-owned Web gate;
5. uses only the repository's Cloudflare account/token secrets for `wrangler deploy`.

New projects default to no automatic preview deployment. Preview automation may be enabled only after protected-preview verification.

## 7. Executable provisioner

`providers/infrastructure/provisioning.py` uses the same `project.infrastructure.json` desired state as the existing reconciliation layer.

It performs or plans these phases:

1. verify the external-CI profile;
2. verify account-wide Access before mutation;
3. create the GitHub repository as private when absent;
4. create Worker metadata when absent;
5. inspect only GitHub secret metadata, never secret values;
6. return `SECRET_BROKER_REQUIRED` until the two deployment secrets are installed;
7. return `READY_FOR_CI` once the project is ready for GitHub Actions deployment.

The provisioner does not create a public release and does not bypass publication gates.

## 8. Verification

A restricted project is not complete merely because CI passed.

Verify:

- the intended GitHub repository remains private;
- account-wide Worker protection still exists;
- the deployed Worker revision is the intended revision;
- anonymous production access is challenged or denied;
- if previews are enabled, anonymous preview access is challenged or denied;
- direct assets do not bypass the access layer;
- no deployment token appears in Git, logs, issues, PRs, or chat;
- rollback is recorded.

Public release uses the separate PPF publication gate and must not be inferred from successful deployment.

## 9. Native Workers Builds remains supported

`workers-builds-native` remains the convenience/provider-native profile and has real pilot evidence in this repository.

It is appropriate when minimal provider setup is more important than one-Worker credential isolation. Workers Builds currently uses a user-token model for build credentials.

The external-CI profile remains attractive for deliberately agent-provisioned projects because the provisioning principal can create the Worker first and then install a token scoped to that Worker only. It is not the default onboarding path for ordinary personal-account projects.

## 10. Current evidence boundary

Repository implementation and offline/CI tests can establish that the contracts are internally consistent. The project provisioner and atomic Secret Broker orchestration are implemented and testable, but the Cloudflare granular-token issuer adapter still requires live provider acceptance. These facts do **not** establish a live end-to-end new-project deployment.

Before changing this profile from “implemented reference profile” to “verified default”, run one clean pilot from an empty project request through:

```text
new private repo
-> Worker creation
-> secret broker
-> GitHub Actions deploy
-> restricted anonymous denial
-> revision verification
-> durable state write-back
```

Record the exact provider evidence and rollback point. Until that pilot succeeds, do not describe Profile B as production-accepted.

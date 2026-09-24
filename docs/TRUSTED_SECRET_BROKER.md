# Trusted Secret Broker Contract

**Status:** executable orchestration implemented; Cloudflare granular-token policy adapter pending live acceptance  
**Request schema:** `ppf/secret-broker-request/v1`  
**Result schema:** `ppf/secret-broker-result/v1`

The Secret Broker is the only boundary allowed to see project deployment-token plaintext in the `agent-provisioned-external-ci` profile.

It is not an LLM prompt and not project repository state.

## 1. Why this boundary exists

Creating an account-owned Cloudflare token is a high-privilege platform operation. The resulting project credential should be much narrower: one existing Worker, `Editor`, suitable for routine Wrangler deployment.

The platform therefore separates:

```text
high-privilege token minting authority
        |
        v
trusted Secret Broker
        |
        +--> project-scoped Worker Editor credential
        |
        +--> GitHub Actions encrypted secret store
```

The project Agent receives only non-secret status/identifiers.

## 2. Implemented state machine

The executable orchestration is:

`providers/infrastructure/secret_broker.py`

It accepts the non-secret request emitted by the PPF Project Provisioner and requires two injected trusted adapters:

- `WorkerTokenIssuer`
- `RepositorySecretWriter`

The broker itself does not guess Provider policy JSON.

### Success path

1. validate the request and plaintext-safety rules;
2. confirm neither target GitHub Secret already exists;
3. ask the trusted token issuer for an account-owned credential scoped to the requested existing Worker with `Editor`;
4. reject and revoke the token if the issuer returns a broader/mismatched scope;
5. write `CLOUDFLARE_API_TOKEN`;
6. write `CLOUDFLARE_ACCOUNT_ID`;
7. re-read Secret metadata and verify both names exist;
8. return only `ppf/secret-broker-result/v1` non-secret metadata;
9. best-effort wipe the mutable token buffer.

### Failure path

If a write fails after minting:

1. delete only Secrets written during this broker execution;
2. revoke the newly minted Cloudflare token;
3. return `ROLLED_BACK` if cleanup completed;
4. return `ROLLBACK_INCOMPLETE` with sanitized non-secret rollback markers if cleanup could not be completed.

The broker refuses to overwrite a pre-existing target Secret. This avoids deleting an older credential during rollback.

## 3. Request safety rules

Every request requires:

```text
plaintextMustNotEnterModelContext = true
plaintextMustNotEnterGit = true
discardPlaintextAfterEncryptedWrite = true
existingSecretsMustNotBeOverwritten = true
rollbackMustRevokeMintedToken = true
```

The only accepted target secret names are:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

## 4. Cloudflare token issuer adapter

The issuer runs inside the trusted broker boundary.

Current Cloudflare documentation establishes:

- account-owned tokens are created through `POST /accounts/{account_id}/tokens`;
- token creation requires Account API Tokens write authority;
- creating/updating account-owned tokens is a Super Administrator capability at the account role level;
- individual-Worker permissions are available for account-owned API tokens;
- `Editor` can update/deploy an existing Worker but cannot create or delete Workers;
- a Worker must exist before a per-Worker role can be assigned.

Therefore the issuer MUST:

1. receive an already-existing Worker ID/name from the PPF Provisioner;
2. discover/validate the current Provider permission-group and resource-selector representation;
3. mint only an account-owned token for the specified Worker with `Editor`;
4. verify the returned non-secret token policy/identity before allowing installation;
5. return token plaintext only as in-process secret material to the broker;
6. support token revocation by non-secret token ID.

### No guessed policy JSON

Cloudflare's public documentation confirms the capability but does not provide a stable complete JSON example for the new “Specified Workers + Editor” policy encoding.

PPF therefore deliberately does **not** hard-code an inferred resource selector in the reference implementation.

The first live pilot must capture the exact current API shape through an authorized provider interaction, verify it against the requested Worker, and only then implement/freeze the Cloudflare issuer adapter.

This is a safety property, not missing authorization for the rest of the provisioning model.

## 5. GitHub Actions Secret writer adapter

GitHub's REST API requires repository Secret values to be encrypted with the repository's public key before create/update.

A concrete writer must:

1. request the repository Actions Secret public key;
2. encrypt the value with libsodium sealed-box semantics;
3. PUT the encrypted value and key ID through the repository Actions Secrets endpoint;
4. expose only Secret-name metadata for verification;
5. support deletion of Secrets created during the current broker transaction.

The writer must never return decrypted/previous Secret values.

The project Agent should normally need only Secret metadata read access. The trusted broker identity needs the write authority.

## 6. Process isolation

A production broker SHOULD run as a short-lived isolated process/service invocation.

It must not:

- print request credentials;
- print Provider response bodies that may contain token material;
- persist plaintext token values;
- include plaintext in exception messages;
- expose the token through model/tool output;
- accept token values through chat.

Provider errors must be converted to sanitized error codes.

## 7. Result contract

Safe result fields include:

- installation status;
- repository;
- Worker non-secret ID;
- minted token non-secret ID;
- installed Secret names;
- Secret-metadata verification status;
- rollback state and sanitized rollback errors.

`plaintextReturned` is always `false`.

## 8. Acceptance requirements

The Secret Broker part of the live new-project pilot passes only if:

- the Worker already exists before minting;
- the actual token is verified as individual-Worker `Editor`;
- both GitHub Secrets are installed without plaintext appearing in Agent output/logs/Git;
- deployment succeeds with that credential;
- the credential cannot modify an unrelated Worker;
- a forced second-secret write failure revokes the new token and removes only the first Secret written by that transaction;
- rerunning against already-present Secrets blocks rather than overwriting them.

Until the Provider-specific issuer passes this live acceptance, report:

`secret_broker_orchestration: implemented`  
`cloudflare_granular_token_issuer: live-acceptance-pending`

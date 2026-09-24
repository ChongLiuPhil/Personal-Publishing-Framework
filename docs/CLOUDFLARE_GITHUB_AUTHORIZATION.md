# GitHub + Cloudflare Platform Authorization Guide (PPF Reference)

**Reviewed:** 2026-09-24

The goal is to minimize repeated human authorization for future projects while keeping provider authority bounded.

PPF now distinguishes two supported routes:

1. **Agent-provisioned external CI** — preferred for future projects created by an AI Agent.
2. **Workers Builds Native** — provider-native alternative with existing real-pilot evidence.

`cloudflare-builds.yaml` remains a PPF machine contract. Cloudflare does not automatically consume it.

## 1. Preferred route for future agent-provisioned projects

```text
Human
  |
  +-- authorize GitHub provisioning principal once
  |
  +-- authorize Cloudflare provisioning principal once
          |
          v
      Project Provisioner
       /            \
 GitHub              Cloudflare
 private repo        all_workers baseline check
 workflow            Worker creation
 repo secrets <---- trusted secret broker
       \             /
        GitHub Actions
             |
        wrangler deploy
```

No Cloudflare GitHub App installation is required for each new project in this profile.

See [AGENT_PROVISIONED_EXTERNAL_CI.md](AGENT_PROVISIONED_EXTERNAL_CI.md).

## 2. One-time GitHub platform authorization

Prefer a dedicated GitHub organization or another clearly bounded installation scope.

Authorize a provisioning GitHub App with only the capabilities needed by the implementation. Typical required repository permissions are:

```text
Administration: write
Contents: write
Workflows: write
Actions: write
Secrets: write
Pull requests: write
Metadata: read
```

The exact permission set must be verified against the operations actually implemented.

Completion criterion:

> The provisioning principal can create and configure a private project repository inside the approved scope without another repository-by-repository human authorization.

Do not install the App on unrelated organizations/accounts merely for convenience.

## 3. One-time Cloudflare platform authorization

Authorize one Cloudflare provisioning principal through an API token, OAuth, or an official MCP connection supported by the executing client.

The platform principal may need authority to:

- inspect account and Worker inventory;
- read Access applications;
- create Worker metadata;
- create account-owned API tokens;
- read deployment and observability state;
- create/update Access applications only when separately authorized;
- attach a domain only when domain/DNS authority has been explicitly granted.

Creating a new Worker requires Workers product-level Admin. Routine deployment must not continue using that broad identity.

Completion criterion:

> The provisioner can verify the account-wide Access baseline and create a Worker, while project deployments can later use a credential restricted to that Worker.

## 4. Account-wide private baseline before project creation

Before provisioning new project Workers, configure and verify a Cloudflare Access application whose destination covers `all_workers` or an equivalent account-wide baseline.

This is a platform bootstrap action, not a per-project publication decision.

A project provisioner must fail closed if it cannot verify that future Workers will be protected by default.

Do not create a public bypass merely to make provisioning easier.

## 5. Project-scoped deployment credential

After the platform principal creates the Worker, create an account-owned API token scoped to:

```text
resource: individual Worker
role: Editor
```

The token is the recurring project deployment identity.

It should not have authority to:

- create unrelated Workers;
- modify unrelated Workers;
- change account-wide Access;
- change zones/routes unless the deployment contract actually requires that authority.

## 6. Secret broker requirement

The project token and account ID belong in GitHub Actions secrets, but token plaintext must not pass through the language model.

The executable provisioner returns only a non-secret `secretBrokerRequest`.

A trusted broker must:

1. create the Cloudflare token;
2. hold plaintext only inside the broker process;
3. obtain the GitHub repository public key or otherwise use the provider's secure secret-write mechanism;
4. write `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`;
5. discard token plaintext;
6. return only non-secret installation status and IDs.

Never ask the user to paste this token into chat.

## 7. Restricted deployment after platform bootstrap

After the two platform authorizations exist, a new project should normally require no additional account-level consent.

The Agent may:

- create the private GitHub repository;
- initialize the PPF/Starter project;
- create the Worker;
- request the secret broker;
- run the GitHub Actions deployment;
- verify anonymous Access denial;
- write non-secret provider state back to the project.

Public release is still a separate human publication decision.

## 8. Workers Builds Native alternative

For projects that deliberately choose provider-native Git integration:

```text
AI Agent / operator
   |
   +--> Cloudflare
           |
           +--> Workers Builds
                    |
                    +--> Cloudflare GitHub App
                            |
                            +--> selected repository
```

The Cloudflare GitHub App authorization is required for this route.

After that authorization, Workers Builds configuration, repository connection, triggers, builds, and monitoring can be managed through the provider API where supported.

Workers Builds currently uses a user-token model for its build credential. Do not describe that credential as one-Worker least privilege.

## 9. Cloudflare MCP

When the client supports official Cloudflare MCP, it is a useful way to establish or operate the Cloudflare provisioning principal.

Relevant official endpoints include:

```text
https://mcp.cloudflare.com/mcp
https://builds.mcp.cloudflare.com/mcp
```

MCP availability does not change the authorization boundary: login/MFA and consent remain human-owned; secrets must remain outside chat/model context.

## 10. Human-reserved gates after bootstrap

Do not return to the human for ordinary project creation merely because a new repository or Worker exists inside the approved platform scope.

Return to the human when the action changes a reserved boundary, including:

- public publication;
- new/expanded reader audience;
- new canonical domain or DNS authority;
- new GitHub organization/App installation scope;
- new Cloudflare permission scope;
- paid-plan/billing change;
- direct secret input if a trusted broker is unavailable.

For the full minimal-human contract, see the Starter project-provisioning contract and Cloudflare handoff.

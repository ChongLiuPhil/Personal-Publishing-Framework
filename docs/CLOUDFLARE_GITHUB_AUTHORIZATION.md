# Cloudflare ↔ GitHub One-Time Authorization Guide (PPF Reference)

This guide is written for an operator with no technical background.

The goal is not to teach APIs, Wrangler, or CI. The human should complete only the account-owner authorization actions that cannot safely be delegated. After that, an AI agent with Cloudflare MCP access should continue from the repository's machine-readable contract.

## Recommended route

```text
AI Agent
   |
   +--> Cloudflare OAuth / MCP
   |
Cloudflare account
   |
   +--> Workers Builds
            |
            +--> GitHub App
                    |
                    +--> selected repository only
```

Cloudflare API MCP:

`https://mcp.cloudflare.com/mcp`

Workers Builds MCP:

`https://builds.mcp.cloudflare.com/mcp`

The project's `cloudflare-builds.yaml` is a **PPF machine contract**. Cloudflare does not automatically consume that file. An AI agent or human operator must apply its values to Workers Builds.

## Authorization 1: connect the AI agent to Cloudflare

If the AI client supports MCP:

1. Open its Plugins / Connectors / MCP / Integrations settings.
2. Add the official Cloudflare MCP server.
3. A Cloudflare sign-in and authorization page should open.
4. Sign in to your Cloudflare account.
5. If permission selection is offered, keep only the permissions needed for Workers / Workers Builds management. Do not add unrelated DNS, R2, KV, or D1 access without a reason.
6. Approve the connection.
7. Return to the AI client.

Completion criterion:

> The AI agent can actually read Cloudflare account, Workers, or Workers Builds state.

If the AI client does not support Cloudflare MCP, use the Dashboard fallback below.

## Authorization 2: allow Cloudflare to access the selected GitHub repository

1. Open the Cloudflare Dashboard.
2. Go to Workers & Pages.
3. Create a Worker with **Import a repository**, or connect a Git repository from the Builds settings of an existing Worker.
4. Select GitHub.
5. GitHub will show the Cloudflare Workers & Pages App authorization page.
6. If GitHub offers **All repositories** or **Only select repositories**, choose **Only select repositories**.
7. Select only the repository needed for the PPF project.
8. Complete the authorization and return to Cloudflare.

Completion criterion:

> Cloudflare can see the project repository but does not have access to unrelated repositories.

## After both authorizations

If the AI agent can call Cloudflare MCP, tell it:

> “Cloudflare OAuth and the GitHub App are authorized. Configure Workers Builds and run the first preview validation from the repository's `cloudflare-builds.yaml`.”

The AI should then:

- confirm or create the Worker;
- verify the Git repository connection;
- configure the production branch;
- configure build / deploy / preview-deploy commands;
- enable non-production branch builds when required;
- trigger the first build;
- inspect build logs;
- verify the preview / workers.dev URL;
- write the real status back to the project's readiness state.

## Dashboard fallback

If the AI client cannot use Cloudflare MCP, configure Workers Builds in the Cloudflare Dashboard.

Copy these values from `cloudflare-builds.yaml`:

- Worker name;
- GitHub repository;
- production branch;
- root directory;
- build command;
- deploy command;
- preview deploy command.

Do not recreate them from memory and do not casually change them.

## Token safety

The reference rules are:

- tokens never enter Git;
- tokens are not pasted into chat;
- tokens are not written into README files;
- tokens are not stored in `cloudflare-builds.yaml`;
- GitHub App access should be limited to selected repositories where practical;
- custom token permissions should be narrowly scoped;
- one-time provisioning authority should be separated from recurring deployment authority.

## Do not do these before the first preview validation

- do not attach the final Custom Domain;
- do not change DNS;
- do not retire the existing production site;
- do not change the canonical URL;
- do not treat a preview as a production cutover.

If the live UI differs from this guide, do not guess. Record the page title and visible options and ask the AI agent or project maintainer to reconcile the difference.

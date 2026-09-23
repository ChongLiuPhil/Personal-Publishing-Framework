# GitHub–Cloudflare Infrastructure Integration

PPF projects declare hosting intent in `project.infrastructure.json`. The manifest is desired state; GitHub and Cloudflare API responses plus anonymous HTTP probes are actual state. Provider adapters read actual state first, the planner emits the smallest idempotent reconciliation plan, and an orchestrator may apply only operations whose authorization and release gates have passed.

For setup by a web AI agent working from GitHub, use the [web-agent onboarding contract](WEB_AGENT_GITHUB_CLOUDFLARE_ONBOARDING.md). It defines discovery, minimum project inputs, safe apply boundaries, live verification, and rollback.

## Visibility and safe defaults

Repository and application visibility are independent fields. A public site does not make its GitHub repository public, and an open repository does not make its hosted application public. New projects default to a private repository, private production Worker, private previews, no public bypass, no paid services, and an account-wide Access baseline. Preview protection is independent from production visibility.

`release.state: public` records intended public state; by itself it is not an approval. Public transitions require an upstream approval identifier and the relevant publication gate. Repository publication additionally requires content, license, privacy, and secret/history checks. Website publication requires its own gate and verification that a control Worker remains private. Account-wide Access is a platform bootstrap boundary; project reconciliation must not enable or disable it.

## Files and commands

- `schema/project.infrastructure.schema.json` defines the machine-readable desired-state contract.
- `templates/quarto-book/project.infrastructure.json` is the private-by-default example.
- `schema/integration-state.schema.json` defines provider IDs recorded in private local state.
- `providers/infrastructure/manifest.py` validates the manifest.
- `providers/infrastructure/plan.py` compares desired state with a provider-read snapshot and emits a read-only plan.
- `providers/infrastructure/state.py` stores non-secret IDs and audit events under `~/.ppf/infrastructure` (or `PPF_INFRA_STATE_DIR`) with owner-only permissions.
- `providers/infrastructure/github.py`, `cloudflare.py`, and `coordinator.py` provide injectable GitHub, Workers, Workers Builds, and Access adapters with the `doctor / plan / apply / verify / rollback` commands.

```sh
python providers/infrastructure/manifest.py project.infrastructure.json
python -m providers.infrastructure.plan project.infrastructure.json --actual actual-state.json
python -m providers.infrastructure.coordinator doctor project.infrastructure.json
python -m providers.infrastructure.coordinator plan project.infrastructure.json --website-gate approval.json --build-config builds.json --triggers triggers.json
python -m providers.infrastructure.coordinator apply project.infrastructure.json --website-gate approval.json --build-config builds.json --triggers triggers.json
python -m providers.infrastructure.coordinator verify project.infrastructure.json
python -m providers.infrastructure.coordinator rollback project.infrastructure.json
```

Set GitHub's GITHUB_TOKEN and Cloudflare's CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID directly in the agent's protected process environment. These credentials are never accepted as command-line arguments. Set PPF_PRODUCTION_HOSTNAME, PPF_PREVIEW_URL, and PPF_CONTROL_WORKER_URL for live anonymous verification; they contain hostnames only. The API client returns sanitized error codes, not raw provider messages.

The planner never mutates provider state. Missing actual state returns `READ_REQUIRED`; absent account-wide Access blocks apply; unexpected public state is reported as `SECURITY_DRIFT`. The account-wide Access setup method deliberately stops with `ACCOUNT_SECURITY_UI_APPROVAL_REQUIRED`: only the account owner completes that setting in Cloudflare's dashboard. The adapters re-read and verify it afterward. State and audit records reject secret-bearing fields and credential-like values. Build configuration snapshots omit secret environment variables because Cloudflare does not return their values; rollback never rewrites or records them.

## Provider behavior

Cloudflare Access can protect all Workers through an account-level all_workers destination. A public production hostname under that baseline needs a separate exact-hostname public destination with a bypass policy. A worker destination covers both production and previews; the more-specific public destination takes precedence, so an exact production hostname bypass leaves preview hostnames covered by the account baseline. Keep the baseline active. Bypass disables Access enforcement and Access request logging for matching traffic, so public applications need Worker observability. Always verify the public target and a separate private control Worker after a public transition.

Workers Builds identifies a Worker by its immutable `external_script_id` tag, not by its name. Store the Worker name, tag, repository ID, connection UUID, trigger UUIDs, and build-token UUID as separate values. The build-token UUID is an identifier, not a secret value. Cloudflare's current Workers Builds API requires a user-scoped API token with Workers Builds Configuration Edit and Workers Scripts Read for its documented provisioning flow; do not describe that credential as least privilege. GitHub visibility writes require repository Administration write permission. Keep these credentials out of source control and logs.

GitHub App installation/authorization, account-wide Access bootstrap, domain/DNS, billing, and final public transitions remain explicit gates. `apply` must not infer permission to perform any of them from a build, deploy, sync, or update request. No Pages resource is automatically migrated or deleted.

## Current implementation boundary

Provider adapters now read GitHub repositories, Workers, Workers Builds configuration/triggers, and Access applications. GitHub visibility, Workers Builds configuration/triggers, and the exact production-hostname Access exception reconcile by re-reading before writes. Account-wide Access remains a manual Cloudflare dashboard action. Worker code deployment is left to the repository's approved build pipeline. Live apply/verify requires provider credentials, the account-wide Access UI gate, and the appropriate explicit publication gate; simulation tests do not count as live verification.

Current provider references (checked 2026-09-23):

- Cloudflare Workers Access: <https://developers.cloudflare.com/workers/configuration/cloudflare-access/>
- Cloudflare Workers Builds API: <https://developers.cloudflare.com/workers/ci-cd/builds/api-reference/>
- Cloudflare Workers best practices: <https://developers.cloudflare.com/workers/best-practices/workers-best-practices/>
- GitHub repository API: <https://docs.github.com/en/rest/repos/repos>

# GitHub–Cloudflare Infrastructure Integration

PPF projects declare hosting intent in `project.infrastructure.json`. The manifest is desired state; GitHub and Cloudflare API responses plus anonymous HTTP probes are actual state. Provider adapters read actual state first, the planner emits the smallest idempotent reconciliation plan, and an orchestrator may apply only operations whose authorization and release gates have passed.

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

```sh
python providers/infrastructure/manifest.py project.infrastructure.json
python -m providers.infrastructure.plan project.infrastructure.json --actual actual-state.json
```

The planner never mutates provider state. Missing actual state returns `READ_REQUIRED`; account-wide Access gaps return `BOOTSTRAP_REQUIRED`; unexpected public state is reported as `SECURITY_DRIFT`. State and audit records reject secret-bearing fields and credential-like values. Never put API tokens, passwords, cookies, private keys, or raw provider error bodies in state or logs.

## Provider behavior

Cloudflare Access can protect all Workers through an account-level `all_workers` destination. A public production Worker under that baseline needs a Worker-scoped `worker` destination with a bypass policy; the account baseline remains active. Previews can be protected separately. Bypass disables Access enforcement and Access request logging for matching traffic, so public applications need Worker observability. Always verify the public target and a separate private control Worker after a public transition.

Workers Builds identifies a Worker by its immutable `external_script_id` tag, not by its name. Store the Worker name, tag, repository ID, connection UUID, trigger UUIDs, and build-token UUID as separate values. The build-token UUID is an identifier, not a secret value. Cloudflare's current Workers Builds API requires a user-scoped API token with Workers Builds Configuration Edit and Workers Scripts Read for its documented provisioning flow; do not describe that credential as least privilege. GitHub visibility writes require repository Administration write permission. Keep these credentials out of source control and logs.

GitHub App installation/authorization, account-wide Access bootstrap, domain/DNS, billing, and final public transitions remain explicit gates. `apply` must not infer permission to perform any of them from a build, deploy, sync, or update request. No Pages resource is automatically migrated or deleted.

## Current implementation boundary

The manifest validator, visibility invariants, read-only planner, private ID/audit store, and existing Cloudflare Worker lifecycle adapter are implemented and tested. Provider inventory readers and mutating GitHub/Cloudflare reconciliation operations are not yet implemented by this reference package; until then, operators must supply an independently verified actual-state snapshot and must not treat a plan as proof that resources exist or have changed.

Current provider references (checked 2026-09-23):

- Cloudflare Workers Access: <https://developers.cloudflare.com/workers/configuration/cloudflare-access/>
- Cloudflare Workers Builds API: <https://developers.cloudflare.com/workers/ci-cd/builds/api-reference/>
- Cloudflare Workers best practices: <https://developers.cloudflare.com/workers/best-practices/workers-best-practices/>
- GitHub repository API: <https://docs.github.com/en/rest/repos/repos>

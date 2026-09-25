# Per-Project GitHub → Cloudflare Setup

**Status:** default onboarding path for new personal-account projects  
**Default delivery profile:** `workers-builds-native`  
**Default source:** private GitHub repository  
**Default Web:** restricted/authenticated Cloudflare Worker  
**UI review date:** 2026-09-25

This guide intentionally does **not** assume account-wide zero-touch provisioning. A small amount of human setup is allowed once per project. After that project bootstrap, normal source pushes should build and deploy automatically.

The advanced `agent-provisioned-external-ci` + Trusted Secret Broker path remains supported as an optional hardening/automation profile, but it is not the default prerequisite.

## 0. Human-operation and write-back rule

If the full Starter stack is present, human-required setup is tracked in `project-bootstrap-state.yaml` and AHICP Working Memory.

Before the human opens a provider UI, the Agent should persist the relevant step as `waiting-human`. After the human returns, the Agent verifies actual provider state and only then marks it completed.

| Human step | Current UI path | Success evidence | Bootstrap-state write-back |
| --- | --- | --- | --- |
| Create private repo | GitHub → **+** → **New repository** | repo exists under `ChongLiuPhil`, visibility Private, branch `main` | `source.repository_state: verified-private` |
| Connect/import repo | Cloudflare → **Workers & Pages** → **Create application** → import existing Git repository | intended repo selected and Worker created/connected | `cloudflare.git_connection: verified` |
| Repair Git repo access | Worker → **Settings > Builds** → **Git Repository > Manage** → GitHub App settings | target private repo becomes selectable | `human_steps.authorize_repository_access: completed` |
| Enable Zero Trust once if needed | Cloudflare → **Zero Trust** onboarding | Zero Trust organization exists | `cloudflare.zero_trust: verified` |
| Protect Worker | **Workers & Pages** → Worker → **Access** → **Protect this Worker behind Access** → **All traffic** | Access shows enabled and anonymous request is challenged/denied | `cloudflare.access_state: verified-private` |
| First deployment verification | Cloudflare build/deployment + Git revision check | intended revision deployed and private | `cloudflare.first_deployment: verified` |
| Second-push verification | push harmless change to `main` | automatic new build/deploy, no renewed authorization | `cloudflare.second_push_auto_deploy: verified` |

Do not store passwords, token values, OAuth codes, OTPs, recovery codes, private keys, cookies, or reader credentials in the bootstrap-state file, Git, or chat.

## 1. Create the project repository

Create the repository under the personal GitHub account that owns the project.

For manual creation in the current GitHub UI:

1. Sign in to GitHub.
2. In the upper-right corner, select **+** → **New repository**.
3. Under **Owner**, select `ChongLiuPhil`.
4. Enter the exact project repository name declared by `project-provisioning.yaml`.
5. Under **Visibility**, select **Private**.
6. If the Agent/Starter will populate the repository, leave optional initialization files (README / .gitignore / license) unselected unless the project already decided otherwise; this avoids unnecessary initial merge conflicts.
7. Select **Create repository**.
8. Confirm the repository page shows the intended `ChongLiuPhil/<repository>` identity and **Private** visibility.
9. Ensure the working default branch is `main` after the project files are pushed.

Default project settings:

```text
Owner: ChongLiuPhil
Visibility: Private
Default branch: main
```

After verification, write back `source.repository_state: verified-private` plus the non-secret repository URL. Do not record GitHub session credentials.

Then apply the Starter/PPF project files and validate the repository contract before Cloudflare is connected.

## 2. Connect the repository in Cloudflare Workers Builds

In the Cloudflare dashboard:

1. Go to **Workers & Pages**.
2. Select **Create application**.
3. Under **Import a repository**, select **Get started**.
4. Choose the GitHub account. If this Git account was already connected to Cloudflare, reuse that connection; Cloudflare documents that the connected Git account can be used for future projects.
5. If the intended private repository is not yet visible, approve or expand the Cloudflare GitHub App's repository access for that repository. Prefer selected-repository access when practical. Do not repeat OAuth merely because this is a new project when the existing connection already works.
6. Select the new private project repository.
7. Configure the project:
   - Worker/application name: exactly the same value as `name` in `wrangler.jsonc` (and the project's declared Cloudflare Worker target)
   - production branch: `main`
   - root directory: `/`
   - build command: `bash scripts/cloudflare_build.sh`
   - deploy command: `npx wrangler deploy`
   - non-production branch builds / previews: disabled by default
8. Select **Save and Deploy**.

If the repository does not appear, open the target Worker and go to **Settings > Builds**. Under **Git Repository**, select **Manage**. GitHub should open the **Cloudflare Workers and Pages** App installation settings; choose repository access that includes the exact target private repository, save the change, then return to Cloudflare and retry repository selection. This is repository-access expansion, not a reason to recreate an already-working Git-account connection. When the repository becomes selectable, write back the repository-access step as completed; do not store OAuth/session material.

No Cloudflare API token needs to be copied into the repository or chat for this default profile. Workers Builds uses the provider-managed build credential.

## 3. Make the Worker private

The default Web state is restricted.

Cloudflare Access requires Zero Trust to be enabled on the account. If this is the first protected Worker and Zero Trust is not yet enabled: open the Cloudflare dashboard → **Zero Trust**; on the onboarding screen choose the account's team name; complete onboarding using the intended plan. If the intended policy is to remain on the Free plan, confirm the UI still shows the Free / $0 option before accepting any billing change. Cloudflare may require payment details even for the Free plan. If the UI instead requires a paid upgrade or materially different billing decision, stop and return that decision to the human. Once the Zero Trust organization exists, write back `cloudflare.zero_trust: verified`. This account prerequisite is reused by later projects.

After the Worker exists:

1. Open **Workers & Pages**.
2. Select the Worker.
3. Open the **Access** tab.
4. Select **Protect this Worker behind Access**.
5. Choose **All traffic** so production and previews are covered.
6. Select the already-approved reusable authentication policy when available; create/configure it only if this account does not yet have the intended policy.
7. Apply Access.

If account-wide **Protect all Workers** is already enabled and verified, this per-Worker step may be skipped. The project should record which Access mode is actually in force:

```text
worker-scoped-access
or
account-wide-access
```

Do not create a public bypass for a private project.

## 4. Verify the first deployment

The project is not ready merely because Cloudflare says a deployment succeeded.

Verify all of the following:

- the GitHub repository is still private;
- the Worker is connected to the intended repository;
- the Cloudflare Worker/application name matches `wrangler.jsonc.name`;
- the production branch is `main`;
- the intended source revision was deployed;
- an anonymous request is challenged or denied by Cloudflare Access;
- authenticated access works for the approved reader;
- direct asset URLs do not bypass Access;
- no credential value appears in Git, issues, PR text, logs, or model/chat context.

Record only non-secret provider IDs, URLs, status, and verification evidence.

## 5. Verify that the project is now automatic

Make one harmless source change and push it to `main`.

Expected result:

```text
Git push
-> Workers Builds starts automatically
-> project build command runs
-> wrangler deploy runs
-> intended revision becomes production
-> Access remains enforced
```

This second deployment should not require the user to reconnect the Git account, reauthorize the Cloudflare GitHub App, or reconnect the same repository.

Once this succeeds, ordinary future source changes may use the same connection.

## 6. Human-reserved changes

The per-project setup does not authorize:

- making the GitHub repository public;
- making the Web publication public;
- adding or expanding readers;
- adding a custom domain or changing DNS;
- expanding provider permissions beyond the project;
- enabling a paid plan or billing change.

Those remain explicit human decisions.

## 7. Optional advanced external-CI profile

Projects that specifically need a project-scoped Cloudflare Worker credential may select:

```text
agent-provisioned-external-ci
```

That profile uses GitHub Actions, a Trusted Secret Broker, and a scoped deployment credential. It has stronger credential isolation but requires more infrastructure and is not the default path for ordinary new projects.

Do not ask the user to paste deployment tokens into chat.

## 8. Durable project-memory write-back

For a full Starter/AHICP project, do not finish a human handoff with only a chat message.

After each verified step:

- update `project-bootstrap-state.yaml`;
- update AHICP Task Plan / Current Focus if the blocker or next action changed;
- append a Work Log milestone after meaningful bootstrap progress;
- keep `memory_writeback.last_sync` at `pending` until the Working Memory projection matches the verified bootstrap state;
- set it to `synchronized` only after the repository memory has been updated.

If the provider works but repository memory is stale, the project is not operationally complete.

## 9. Completion state

The default project bootstrap is complete when the project can truthfully report:

```text
github_repository: private
cloudflare_git_connection: verified
workers_builds: verified
worker_access: verified-private
second_push_auto_deploy: verified
public_release: NOT AUTHORIZED
```

This is a per-project operational contract, not a claim of account-wide zero-touch provisioning.

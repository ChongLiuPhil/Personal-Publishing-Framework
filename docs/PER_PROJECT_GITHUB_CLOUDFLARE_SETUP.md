# Per-Project GitHub → Cloudflare Setup

**Status:** default onboarding path for new personal-account projects  
**Default delivery profile:** `workers-builds-native`  
**Default source:** private GitHub repository  
**Default Web:** restricted/authenticated Cloudflare Worker

This guide intentionally does **not** assume account-wide zero-touch provisioning. A small amount of human setup is allowed once per project. After that project bootstrap, normal source pushes should build and deploy automatically.

The advanced `agent-provisioned-external-ci` + Trusted Secret Broker path remains supported as an optional hardening/automation profile, but it is not the default prerequisite.

## 1. Create the project repository

Create the repository under the personal GitHub account that owns the project.

Default project settings:

```text
Owner: ChongLiuPhil
Visibility: Private
Default branch: main
```

The repository may be created manually in GitHub or by an authorized Agent/connector. The important invariant is that it starts private.

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
   - production branch: `main`
   - root directory: `/`
   - build command: `bash scripts/cloudflare_build.sh`
   - deploy command: `npx wrangler deploy`
   - non-production branch builds / previews: disabled by default
8. Select **Save and Deploy**.

If the repository does not appear, manage the Cloudflare Git installation from the Worker's **Settings > Builds > Git Repository > Manage** or from GitHub's installed-app settings, then grant access to this repository and retry. This is repository-access expansion, not a reason to recreate an already-working Git-account connection.

No Cloudflare API token needs to be copied into the repository or chat for this default profile. Workers Builds uses the provider-managed build credential.

## 3. Make the Worker private

The default Web state is restricted.

Cloudflare Access requires Zero Trust to be enabled on the account. If this is the first protected Worker and Zero Trust is not yet enabled, complete Cloudflare's Zero Trust setup once, then return to the Worker. This is an account prerequisite that later projects reuse; it is not a per-project authorization.

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

## 8. Completion state

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

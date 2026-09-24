# Agent contract

Before configuring or publishing a project, read:

1. [`docs/ECOSYSTEM.md`](docs/ECOSYSTEM.md)
2. [`ecosystem.yaml`](ecosystem.yaml)
3. the [canonical cross-repository agent retrieval contract](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/AGENT_RETRIEVAL_CONTRACT.md)
4. when Continuous Web or Cloudflare is in scope, [`docs/CONTINUOUS_WEB_CLOUDFLARE.md`](docs/CONTINUOUS_WEB_CLOUDFLARE.md), the Starter minimal-human/Work handoff, then the applicable provider-specific PPF runbooks
5. for a **new project**, [`docs/AGENT_PROVISIONED_EXTERNAL_CI.md`](docs/AGENT_PROVISIONED_EXTERNAL_CI.md) and the Starter Project Provisioning Contract; use `agent-provisioned-external-ci` as the preferred provisioning profile after platform bootstrap
6. the project's AHICP entrypoint and selected Starter profile when this PPF layer participates in the full stack

For web-agent GitHub-to-Cloudflare onboarding, also follow [`docs/WEB_AGENT_GITHUB_CLOUDFLARE_ONBOARDING.md`](docs/WEB_AGENT_GITHUB_CLOUDFLARE_ONBOARDING.md) (Chinese: [`docs/WEB_AGENT_GITHUB_CLOUDFLARE_ONBOARDING.zh-CN.md`](docs/WEB_AGENT_GITHUB_CLOUDFLARE_ONBOARDING.zh-CN.md)).

For new projects containing original or unpublished work, the safe default is a private canonical source plus Continuous Web in a restricted, authenticated state. When used through the full Inquiry Publishing Stack, the default composition is full PPF + full AHICP + Vault Interface; reduced profiles require explicit human selection. After the two platform provisioning principals are authorized and account-wide Access is verified, do not ask for repeated account-level consent merely because another project repository or Worker is being created within that approved scope.

From any public PPF entrypoint, reconstruct the four-component ecosystem before cross-component configuration. Public links authorize public retrieval only and never authorize private-state access.

Before a Cloudflare action, state the exact target, affected layer, data flow, credential scope, human approval boundary, verification checks, and rollback path. If human UI interaction is required, provide numbered operator-level instructions with the current Dashboard path, non-secret values to enter, completion evidence, and the next verification step. Never request passwords, tokens, private keys, recovery codes, or other secrets in chat. A Cloudflare deployment token for the external-CI profile must move through a trusted secret broker directly into GitHub Actions secrets; the model receives only non-secret installation status.

Treat human gates as resumable checkpoints, not as a reason to stop the whole task. Continue independent, already-authorized work; when a gate blocks a specific action, give the user its direct provider link, exact navigation steps, required non-secret choices/values, secret-input boundary, completion evidence, and the precise read-back you will perform. Wait only for that gate, then re-read provider state and resume automatically without asking the user to repeat completed steps.

Preserve proposal, authorization, execution, verification, and durable write-back as distinct stages.

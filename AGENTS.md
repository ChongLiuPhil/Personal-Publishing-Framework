# Agent contract

Before configuring or publishing a project, read:

1. [`docs/ECOSYSTEM.md`](docs/ECOSYSTEM.md)
2. [`ecosystem.yaml`](ecosystem.yaml)
3. the [canonical cross-repository agent retrieval contract](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/AGENT_RETRIEVAL_CONTRACT.md)
4. when Continuous Web or Cloudflare is in scope, [`docs/CONTINUOUS_WEB_CLOUDFLARE.md`](docs/CONTINUOUS_WEB_CLOUDFLARE.md), then the applicable provider-specific PPF runbooks
5. the project's AHICP entrypoint and selected Starter profile when this PPF layer participates in the full stack

For new projects containing original or unpublished work, the safe default is a private canonical source plus Continuous Web in a restricted, authenticated state. When used through the full Inquiry Publishing Stack, the default composition is full PPF + full AHICP + Vault Interface; reduced profiles require explicit human selection.

From any public PPF entrypoint, reconstruct the four-component ecosystem before cross-component configuration. Public links authorize public retrieval only and never authorize private-state access.

Before a Cloudflare action, state the exact target, affected layer, data flow, credential scope, human approval boundary, verification checks, and rollback path. If human UI interaction is required, provide numbered operator-level instructions with the current Dashboard path, non-secret values to enter, completion evidence, and the next verification step. Never request passwords, tokens, private keys, recovery codes, or other secrets in chat.

Preserve proposal, authorization, execution, verification, and durable write-back as distinct stages.

# Agent contract

Before configuring or publishing a project, read:

1. [`docs/ECOSYSTEM.md`](docs/ECOSYSTEM.md)
2. [`ecosystem.yaml`](ecosystem.yaml)
3. [`docs/CONTINUOUS_WEB_CLOUDFLARE.md`](docs/CONTINUOUS_WEB_CLOUDFLARE.md) when Continuous Web or Cloudflare is in scope
4. The project's AHICP entrypoint and the selected Starter profile

The default new-project baseline is full PPF plus full AHICP. Do not copy private project state into this repository. Treat original unpublished work as private by default.

Before a Cloudflare action, state the target, data flow, credential scope, human approval boundary, verification checks, and rollback path. Never request passwords, tokens, private keys, or recovery codes in chat.

An agent may follow public ecosystem links for understanding, but private-state retrieval and publication require explicit human authorization. Preserve proposal, authorization, execution, verification, and durable write-back as distinct stages.

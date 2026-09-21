# PPF in the Inquiry Publishing Stack

PPF governs the lifecycle from durable source through build, publication, release, archive, and Continuous Web. It does not define how humans and AI should collaborate.

If the full stack is new to you, start with the [AHICP homepage](https://chongliuphil.github.io/AI-Assisted-Human-Inquiry-and-Creation-Protocol/). For project setup, adoption, or upgrades, an AI should enter through Starter’s machine entrypoint.

For a complete project configuration, follow the [Starter ecosystem entrypoint](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/ECOSYSTEM.md) and connect:

- [AHICP homepage](https://chongliuphil.github.io/AI-Assisted-Human-Inquiry-and-Creation-Protocol/) · [repository](https://github.com/ChongLiuPhil/AI-Assisted-Human-Inquiry-and-Creation-Protocol)
- [Vault Interface homepage](https://chongliuphil.github.io/Vault-interface/) · [repository](https://github.com/ChongLiuPhil/Vault-interface)
- [Starter homepage](https://chongliuphil.github.io/Inquiry-Publishing-Project-Starter/) · [repository](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter)

The default new-project baseline is **full PPF + full AHICP**, with Vault Interface used only for public metadata. A project records actual adoption, source revisions, publication authorization, and provider state in its appropriate project records.

Original unpublished work and other copyright-bearing source assets remain private by default. Continuous Web is a publication capability, not a permission to publish; private or transitional outputs must be protected by reader access control.

For the four public framework sites themselves, Cloudflare Pages is the preferred delivery provider and GitHub remains the canonical source/version-control provider. The current GitHub Pages URLs remain authoritative until the coordinated migration has verified Cloudflare staging, target domains, and cross-project links. This preference does not force downstream projects onto Pages: a downstream publication may use Pages, Workers, or another supported provider according to its actual runtime and publication requirements.

Use the [coordinated public-delivery migration guide](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/CLOUDFLARE_PUBLIC_DELIVERY_MIGRATION.md) for the framework sites.

Use [`CONTINUOUS_WEB_CLOUDFLARE.md`](CONTINUOUS_WEB_CLOUDFLARE.md) for the detailed Cloudflare contract. The existing [security profiles](CLOUDFLARE_SECURITY_PROFILES.md) describe deployment-credential trade-offs; deployment identity and reader access are separate decisions.

For cross-component work, read the [canonical agent retrieval contract](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/AGENT_RETRIEVAL_CONTRACT.md). Public links support ecosystem reconstruction; they do not authorize private-state access.

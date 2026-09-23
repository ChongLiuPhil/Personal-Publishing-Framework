# PPF in the Inquiry Publishing Stack

PPF governs the lifecycle from durable source through build, publication, release, archive, and Continuous Web. It does not define how humans and AI should collaborate.

If the full stack is new to you, start with the [AHICP homepage](https://inquirystack.philohub.workers.dev/). For project setup, adoption, or upgrades, an AI should enter through Starter’s machine entrypoint.

For a complete project configuration, follow the [Starter ecosystem entrypoint](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/ECOSYSTEM.md) and connect:

- [AHICP homepage](https://inquirystack.philohub.workers.dev/) · [repository](https://github.com/ChongLiuPhil/AI-Assisted-Human-Inquiry-and-Creation-Protocol)
- [Vault Interface homepage](https://inquirystack.philohub.workers.dev/vault-interface/) · [repository](https://github.com/ChongLiuPhil/Vault-interface)
- [Starter homepage](https://inquirystack.philohub.workers.dev/starter/) · [repository](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter)

The default new-project baseline is **full PPF + full AHICP**, with Vault Interface used only for public metadata. A project records actual adoption, source revisions, publication authorization, and provider state in its appropriate project records.

Original unpublished work and other copyright-bearing source assets remain private by default. Continuous Web is a publication capability, not a permission to publish; private or transitional outputs must be protected by reader access control.

For new deployments, Cloudflare Workers Static Assets with Workers Builds is the preferred delivery provider and GitHub remains the canonical source/version-control provider. Cloudflare Pages remains supported for existing projects and is not migrated automatically. The verified canonical framework site now uses https://inquirystack.philohub.workers.dev/; former GitHub Pages URLs remain available as legacy entrypoints. A downstream publication may select Pages, Workers, or another supported provider according to its actual runtime and publication requirements.

Use the [coordinated public-delivery migration guide](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/CLOUDFLARE_PUBLIC_DELIVERY_MIGRATION.md) for the framework sites.

Use [`CONTINUOUS_WEB_CLOUDFLARE.md`](CONTINUOUS_WEB_CLOUDFLARE.md) for the detailed Cloudflare publication contract and [`GITHUB_CLOUDFLARE_INTEGRATION.md`](GITHUB_CLOUDFLARE_INTEGRATION.md) for reusable infrastructure state and reconciliation boundaries. The existing [security profiles](CLOUDFLARE_SECURITY_PROFILES.md) describe deployment-credential trade-offs; deployment identity and reader access are separate decisions.

For cross-component work, read the [canonical agent retrieval contract](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/AGENT_RETRIEVAL_CONTRACT.md). Public links support ecosystem reconstruction; they do not authorize private-state access.

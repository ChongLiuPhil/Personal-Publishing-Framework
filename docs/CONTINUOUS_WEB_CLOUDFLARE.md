# Continuous Web and Cloudflare — PPF entrypoint

This file is the local PPF entrypoint for Cloudflare work. The cross-project operational contract is maintained by the Starter:

https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/CONTINUOUS_WEB_CLOUDFLARE.md

Before a Cloudflare operation, read that shared contract first. For the shortest account-owner handoff, also read the Starter [minimal-human guide](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/CLOUDFLARE_MINIMAL_HUMAN_HANDOFF.md); for browser-capable execution, use the [Work/browser-agent handoff](https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/CLOUDFLARE_WORK_AGENT_HANDOFF.md).

Then use the PPF provider-specific runbooks:

1. docs/PER_PROJECT_GITHUB_CLOUDFLARE_SETUP.md — default guided setup for a personal-account private project.
2. docs/CLOUDFLARE_GITHUB_AUTHORIZATION.md — per-project Git authorization, Access setup, and the optional advanced External-CI route.
3. docs/AGENT_PROVISIONED_EXTERNAL_CI.md — optional advanced profile for stronger deployment-credential isolation.
3. docs/CLOUDFLARE_SECURITY_PROFILES.md — deployment credential profiles and least-privilege trade-offs.
4. docs/CLOUDFLARE_ACCESS_PROFILE.md — reader-access mapping.
5. docs/CLOUDFLARE_OBSERVED_UI_MAPPING.md — dated Cloudflare UI observations.

## Agent requirement

If human interaction is necessary, provide numbered operator-level instructions with the exact target account/project/domain, current UI path, non-secret values to select, secret boundary, completion evidence, verification step, and rollback.

Do not ask the human to paste a password, token, private key, recovery code, or other secret into chat. For agent-provisioned external CI, the project deployment token must move through a trusted secret broker directly into GitHub Actions secrets; the model receives only non-secret installation status. If the live Cloudflare UI differs from the dated runbook, verify the current UI or official documentation rather than guessing.

For any newly configured original or unpublished PPF project, the safe default posture is private source + restricted Continuous Web + authenticated access-policy reference. Moving the Web output to public requires explicit human authorization and does not require making the source repository public.

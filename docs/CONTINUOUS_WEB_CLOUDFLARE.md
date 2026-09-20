# Continuous Web and Cloudflare — PPF entrypoint

This file is the local PPF entrypoint for Cloudflare work. The cross-project operational contract is maintained by the Starter:

https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter/blob/main/docs/CONTINUOUS_WEB_CLOUDFLARE.md

Before a Cloudflare operation, read that shared contract first, then use the PPF provider-specific runbooks:

1. docs/CLOUDFLARE_GITHUB_AUTHORIZATION.md — detailed account-owner and GitHub App authorization flow.
2. docs/CLOUDFLARE_SECURITY_PROFILES.md — deployment credential profiles and least-privilege trade-offs.
3. docs/CLOUDFLARE_ACCESS_PROFILE.md — reader-access mapping.
4. docs/CLOUDFLARE_OBSERVED_UI_MAPPING.md — dated Cloudflare UI observations.

## Agent requirement

If human interaction is necessary, provide numbered operator-level instructions with the exact target account/project/domain, current UI path, non-secret values to select, secret boundary, completion evidence, verification step, and rollback.

Do not ask the human to paste a password, token, private key, recovery code, or other secret into chat. If the live Cloudflare UI differs from the dated runbook, verify the current UI or official documentation rather than guessing.

For a Starter-composed original/unpublished project, the default posture is private source + restricted Continuous Web + authenticated access-policy reference. Moving the Web output to public requires explicit human authorization and does not require making the source repository public.

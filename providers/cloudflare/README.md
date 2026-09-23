# PPF Cloudflare lifecycle

The adapter provides `doctor`, `plan`, `apply`, `verify`, and `rollback` for Workers Static Assets. Run it from a project with `publishing.yaml`, `cloudflare-builds.yaml`, and `wrangler.jsonc`:

```sh
python /path/to/ppf/providers/cloudflare/ppf_cloudflare.py doctor
python /path/to/ppf/providers/cloudflare/ppf_cloudflare.py plan
python /path/to/ppf/providers/cloudflare/ppf_cloudflare.py apply
python /path/to/ppf/providers/cloudflare/ppf_cloudflare.py verify --url https://example.workers.dev
python /path/to/ppf/providers/cloudflare/ppf_cloudflare.py rollback --version-id <previous-verified-version-uuid>
```

`doctor` reads the target Worker and Workers Builds trigger inventory when `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` are provided in the process environment. It suppresses API response bodies and never prints credential values. `apply` calls only the project-pinned deploy command. `rollback` requires an explicit UUID. `verify` records timestamp, URL, HTTP status, and optional `GITHUB_SHA` in `.ppf/cloudflare-deployment.json`; `.ppf/` is ignored and deployment state must remain private.

GitHub App installation and repository authorization are separate human-controlled gates. Existing Pages resources, DNS, canonical URLs, and billing plans are outside this adapter's write scope. Preview builds are intended by default but must only be connected after account-wide Access protection is verified; test an anonymous denial on the real preview URL before treating the preview as protected.

Cloudflare Access is the infrastructure access-control layer. PPF does not provide an application-level shared-password gate for publication assets. A Worker with real user accounts may implement application authentication as a separate product feature.

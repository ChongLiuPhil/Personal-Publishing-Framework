# PPF Cloudflare lifecycle

The adapter provides `doctor`, `plan`, `apply`, `verify`, and `rollback` for Workers Static Assets. Run it from a project with `publishing.yaml`, `cloudflare-builds.yaml`, and `wrangler.jsonc`:

```sh
python /path/to/ppf/providers/cloudflare/ppf_cloudflare.py doctor
python /path/to/ppf/providers/cloudflare/ppf_cloudflare.py plan
python /path/to/ppf/providers/cloudflare/ppf_cloudflare.py apply
python /path/to/ppf/providers/cloudflare/ppf_cloudflare.py verify --url https://example.workers.dev
python /path/to/ppf/providers/cloudflare/ppf_cloudflare.py rollback --version-id <previous-verified-version-uuid>
```

`doctor` reads the target Worker and Workers Builds trigger inventory when `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` are provided in the process environment. It suppresses API response bodies and never prints credential values. `apply` calls only the project-pinned deploy command, and does not create a Git connection or enable previews. `rollback` requires an explicit UUID. `verify` records timestamp, URL, HTTP status, and optional `GITHUB_SHA` in `.ppf/cloudflare-deployment.json`; review that generated record before committing it.

GitHub App installation and repository authorization are separate human-controlled gates. Existing Pages resources, DNS, canonical URLs, and billing plans are outside this adapter's write scope. Preview deployment must remain disabled until its Access policy has been configured and tested independently.

The optional `password_gate.mjs` intercepts every static request when paired with `assets.run_worker_first: true`. It uses the Workers `crypto.subtle.timingSafeEqual()` API, signed 12-hour HttpOnly/Secure/SameSite cookies, constant-time password/session checks, an origin check on login, and a Cloudflare Rate Limiting binding. Both secret bindings are mandatory; missing or invalid configuration returns 503. Responses are marked `private, no-store`, including static downloads. The configured five-per-minute rate limit is per IP and per Cloudflare location; Cloudflare documents these limits as permissive/eventually consistent and notes that shared IP addresses may group readers. Do not use it as a global abuse-control or accounting system. Give each project a distinct account-scoped rate-limit namespace ID. Because every static request executes Worker code, this profile consumes Workers request quota; if the account quota is exhausted, stop and report it rather than bypassing the gate or upgrading automatically.

Set secrets through Wrangler's interactive secret command or the Cloudflare dashboard; provide their values directly to Cloudflare and never to this CLI, chat, logs, or Git. The sample Wrangler config is opt-in and its rate-limit namespace ID must be replaced with a unique positive integer before deployment.

import assert from "node:assert/strict";
import { test } from "node:test";
import { timingSafeEqual, webcrypto } from "node:crypto";
import worker, { issueSession, validSession } from "../password_gate.mjs";

if (typeof webcrypto.subtle.timingSafeEqual !== "function") {
	Object.defineProperty(webcrypto.subtle, "timingSafeEqual", { value: timingSafeEqual });
}

const password = "correct-horse-battery";
const signingKey = "test-only-signing-key-with-more-than-thirty-two-bytes";
const baseEnv = () => ({
	PPF_ACCESS_PASSWORD: password,
	PPF_SESSION_SIGNING_KEY: signingKey,
	ASSETS: { fetch: async () => new Response("private file", { headers: { "Content-Type": "application/pdf", "Content-Disposition": "attachment; filename=paper.pdf", "Cache-Control": "public, max-age=86400" } }) },
	LOGIN_LIMIT: { limit: async () => ({ success: true }) },
});

function request(path, options = {}) {
	return new Request(`https://project.example${path}`, options);
}

test("missing secrets or gate bindings fail closed", async () => {
	const env = baseEnv();
	delete env.PPF_SESSION_SIGNING_KEY;
	const response = await worker.fetch(request("/"), env);
	assert.equal(response.status, 503);
	assert.match(response.headers.get("cache-control"), /no-store/);
});

test("wrong password does not create an authenticated session", async () => {
	const env = baseEnv();
	const response = await worker.fetch(request("/__ppf/login", {
		method: "POST",
		headers: { Origin: "https://project.example", "CF-Connecting-IP": "192.0.2.1", "Content-Type": "application/x-www-form-urlencoded" },
		body: new URLSearchParams({ password: "incorrect-password" }),
	}), env);
	assert.equal(response.status, 200);
	assert.match(await response.text(), /password was not accepted/);
	assert.equal(response.headers.get("set-cookie"), null);
});

test("correct password creates a secure, bounded session and serves the asset", async () => {
	const env = baseEnv();
	const login = await worker.fetch(request("/__ppf/login", {
		method: "POST",
		headers: { Origin: "https://project.example", "CF-Connecting-IP": "192.0.2.2", "Content-Type": "application/x-www-form-urlencoded" },
		body: new URLSearchParams({ password }),
	}), env);
	assert.equal(login.status, 303);
	const cookie = login.headers.get("set-cookie");
	assert.match(cookie, /HttpOnly/);
	assert.match(cookie, /Secure/);
	assert.match(cookie, /SameSite=Strict/);
	assert.match(cookie, /Max-Age=43200/);
	const token = cookie.match(/__Host-ppf_session=([^;]+)/u)[1];
	const asset = await worker.fetch(request("/chapter.pdf", { headers: { Cookie: `__Host-ppf_session=${token}` } }), env);
	assert.equal(asset.status, 200);
});

test("rate limited login is rejected before checking credentials", async () => {
	const env = baseEnv();
	env.LOGIN_LIMIT.limit = async () => ({ success: false });
	const response = await worker.fetch(request("/__ppf/login", {
		method: "POST", headers: { Origin: "https://project.example", "CF-Connecting-IP": "192.0.2.1" },
		body: new URLSearchParams({ password }),
	}), env);
	assert.equal(response.status, 429);
});

test("authenticated static attachments cannot use public cache headers", async () => {
	const env = baseEnv();
	const token = await issueSession(env, Math.floor(Date.now() / 1000));
	const response = await worker.fetch(request("/files/paper.pdf", { headers: { Cookie: `__Host-ppf_session=${token}` } }), env);
	assert.equal(response.status, 200);
	assert.equal(response.headers.get("content-disposition"), "attachment; filename=paper.pdf");
	assert.match(response.headers.get("cache-control"), /no-store/);
	assert.doesNotMatch(response.headers.get("cache-control"), /public/);
});

test("expired and rotated sessions are rejected", async () => {
	const env = baseEnv();
	const expired = await issueSession(env, 100);
	assert.equal(await validSession(request("/", { headers: { Cookie: `__Host-ppf_session=${expired}` } }), env, 100 + 12 * 60 * 60), false);
	const active = await issueSession(env, Math.floor(Date.now() / 1000));
	const cookieRequest = request("/", { headers: { Cookie: `__Host-ppf_session=${active}` } });
	env.PPF_ACCESS_PASSWORD = "rotated-password-value";
	assert.equal(await validSession(cookieRequest, env, Math.floor(Date.now() / 1000)), false);
});

test("cross-origin login is rejected", async () => {
	const response = await worker.fetch(request("/__ppf/login", {
		method: "POST", headers: { Origin: "https://attacker.example" }, body: new URLSearchParams({ password }),
	}), baseEnv());
	assert.equal(response.status, 403);
});

const encoder = new TextEncoder();
const COOKIE = "__Host-ppf_session";
const MAX_SESSION_SECONDS = 12 * 60 * 60;
const MAX_LOGIN_BODY = 4096;

function response(body, status, headers = {}) {
	return new Response(body, {
		status,
		headers: {
			"Cache-Control": "private, no-store, max-age=0",
			"Pragma": "no-cache",
			"X-Content-Type-Options": "nosniff",
			"Referrer-Policy": "no-referrer",
			...headers,
		},
	});
}

function base64url(bytes) {
	let binary = "";
	for (const byte of bytes) binary += String.fromCharCode(byte);
	return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/u, "");
}

function fromBase64url(value) {
	if (!/^[A-Za-z0-9_-]+$/u.test(value)) throw new Error("invalid token encoding");
	const padded = value.replaceAll("-", "+").replaceAll("_", "/") + "===".slice((value.length + 3) % 4);
	const binary = atob(padded);
	return Uint8Array.from(binary, (character) => character.charCodeAt(0));
}

async function hmac(keyText, value) {
	const key = await crypto.subtle.importKey("raw", encoder.encode(keyText), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
	return new Uint8Array(await crypto.subtle.sign("HMAC", key, encoder.encode(value)));
}

async function constantTimeEqual(left, right) {
	const [leftHash, rightHash] = await Promise.all([
		crypto.subtle.digest("SHA-256", left),
		crypto.subtle.digest("SHA-256", right),
	]);
	return crypto.subtle.timingSafeEqual(leftHash, rightHash);
}

async function boundedText(request, maxBytes) {
	const reader = request.body?.getReader();
	if (!reader) return "";
	const chunks = [];
	let size = 0;
	while (true) {
		const { done, value } = await reader.read();
		if (done) break;
		size += value.byteLength;
		if (size > maxBytes) {
			await reader.cancel();
			throw new RangeError("request body too large");
		}
		chunks.push(value);
	}
	const body = new Uint8Array(size);
	let offset = 0;
	for (const chunk of chunks) {
		body.set(chunk, offset);
		offset += chunk.byteLength;
	}
	return new TextDecoder().decode(body);
}

function cookieValue(request) {
	const cookies = request.headers.get("Cookie") || "";
	for (const part of cookies.split(";")) {
		const [name, ...rest] = part.trim().split("=");
		if (name === COOKIE) return rest.join("=");
	}
	return "";
}

async function issueSession(env, nowSeconds) {
	const passwordTag = base64url(await hmac(env.PPF_SESSION_SIGNING_KEY, `password\0${env.PPF_ACCESS_PASSWORD}`));
	const payload = base64url(encoder.encode(JSON.stringify({ exp: nowSeconds + MAX_SESSION_SECONDS, passwordTag })));
	const signature = base64url(await hmac(env.PPF_SESSION_SIGNING_KEY, `session\0${payload}`));
	return `${payload}.${signature}`;
}

async function validSession(request, env, nowSeconds) {
	try {
		const [payload, suppliedSignature, extra] = cookieValue(request).split(".");
		if (!payload || !suppliedSignature || extra) return false;
		const expectedSignature = base64url(await hmac(env.PPF_SESSION_SIGNING_KEY, `session\0${payload}`));
		if (!(await constantTimeEqual(encoder.encode(suppliedSignature), encoder.encode(expectedSignature)))) return false;
		const data = JSON.parse(new TextDecoder().decode(fromBase64url(payload)));
		const currentPasswordTag = base64url(await hmac(env.PPF_SESSION_SIGNING_KEY, `password\0${env.PPF_ACCESS_PASSWORD}`));
		const passwordUnchanged = await constantTimeEqual(encoder.encode(data.passwordTag || ""), encoder.encode(currentPasswordTag));
		return Number.isInteger(data.exp) && data.exp > nowSeconds && passwordUnchanged;
	} catch {
		return false;
	}
}

function loginPage(message = "") {
	const notice = message ? `<p role="alert">${message}</p>` : "";
	return response(`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Project access</title><main><h1>Project access</h1>${notice}<form method="post" action="/__ppf/login"><label>Project password <input type="password" name="password" autocomplete="current-password" required></label><button type="submit">Continue</button></form></main></html>`, 200, { "Content-Type": "text/html; charset=utf-8", "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'" });
}

export default {
	async fetch(request, env) {
		if (!env.PPF_ACCESS_PASSWORD || env.PPF_ACCESS_PASSWORD.length < 12 || !env.PPF_SESSION_SIGNING_KEY || encoder.encode(env.PPF_SESSION_SIGNING_KEY).byteLength < 32 || !env.ASSETS || !env.LOGIN_LIMIT) {
			return response("Access protection is not configured.\n", 503);
		}
		const url = new URL(request.url);
		if (url.pathname === "/__ppf/logout") {
			return response("Logged out.\n", 200, { "Set-Cookie": `${COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0`, "Content-Type": "text/plain; charset=utf-8" });
		}
		if (url.pathname === "/__ppf/login" && request.method === "GET") return loginPage();
		if (url.pathname === "/__ppf/login" && request.method === "POST") {
			if (request.headers.get("Origin") !== url.origin) return response("Request rejected.\n", 403);
			const ip = request.headers.get("CF-Connecting-IP") || "unknown";
			try {
				const rate = await env.LOGIN_LIMIT.limit({ key: ip });
				if (!rate.success) return response("Too many attempts. Try again later.\n", 429, { "Retry-After": "60" });
				const text = await boundedText(request, MAX_LOGIN_BODY);
				const params = new URLSearchParams(text);
				const supplied = params.get("password") || "";
				const accepted = await constantTimeEqual(encoder.encode(supplied), encoder.encode(env.PPF_ACCESS_PASSWORD));
				if (!accepted) return loginPage("The password was not accepted.");
				const session = await issueSession(env, Math.floor(Date.now() / 1000));
				return new Response(null, { status: 303, headers: { "Location": "/", "Cache-Control": "private, no-store, max-age=0", "Set-Cookie": `${COOKIE}=${session}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${MAX_SESSION_SECONDS}` } });
			} catch (error) {
				return response(error instanceof RangeError ? "Request too large.\n" : "Access service unavailable.\n", error instanceof RangeError ? 413 : 503);
			}
		}
		if (!(await validSession(request, env, Math.floor(Date.now() / 1000)))) {
			if (request.method === "GET" || request.method === "HEAD") return loginPage();
			return response("Authentication required.\n", 401, { "WWW-Authenticate": 'Form realm="project"' });
		}
		try {
			const asset = await env.ASSETS.fetch(request);
			const headers = new Headers(asset.headers);
			headers.set("Cache-Control", "private, no-store, max-age=0");
			headers.set("X-Content-Type-Options", "nosniff");
			headers.set("Referrer-Policy", "no-referrer");
			return new Response(asset.body, { status: asset.status, statusText: asset.statusText, headers });
		} catch {
			return response("Content service unavailable.\n", 503);
		}
	},
};

export { validSession, issueSession, constantTimeEqual };

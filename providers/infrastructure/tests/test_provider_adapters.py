import unittest

from providers.infrastructure.api import ApiClient, ProviderError
from providers.infrastructure.cloudflare import AccessAdapter, WorkersBuildsAdapter, WorkersAdapter
from providers.infrastructure.github import GitHubAdapter


class FakeTransport:
    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, url, method, headers, body):
        self.calls.append((url, method, headers, body))
        key = (method, url.split("?", 1)[0])
        value = self.routes.get(key)
        if isinstance(value, Exception):
            raise value
        return value


class AdapterTests(unittest.TestCase):
    def test_api_client_never_discloses_provider_error_body(self):
        transport = FakeTransport({("GET", "https://api.example.test/fail"): (403, {"success": False, "errors": [{"message": "secret token"}]})})
        client = ApiClient("https://api.example.test", "TOKEN-SHOULD-NOT-LEAK", transport)
        with self.assertRaises(ProviderError) as caught:
            client.request("GET", "/fail")
        self.assertEqual(str(caught.exception), "HTTP_ERROR")
        self.assertNotIn("TOKEN-SHOULD-NOT-LEAK", str(caught.exception))
        self.assertNotIn("secret token", str(caught.exception))

    def test_github_visibility_patch_is_read_before_write_and_idempotent(self):
        base = "https://api.github.com/repos/a/b"
        transport = FakeTransport({
            ("GET", base): (200, {"private": True, "id": 7}),
            ("PATCH", base): (200, {"private": False}),
        })
        adapter = GitHubAdapter(ApiClient("https://api.github.com", "token", transport))
        adapter.ensure_repository("a", "b", "public", {"allowed": True, "approvalId": "release-1"})
        methods = [call[1] for call in transport.calls]
        self.assertEqual(methods, ["GET", "PATCH", "GET"])

    def test_github_user_repository_creation_uses_user_endpoint(self):
        repo = "https://api.github.com/repos/alice/project"
        create = "https://api.github.com/user/repos"
        transport = FakeTransport({
            ("GET", repo): (404, {"message": "not found"}),
            ("POST", create): (201, {"id": 8, "private": True}),
        })
        adapter = GitHubAdapter(ApiClient("https://api.github.com", "token", transport))
        result = adapter.ensure_repository("alice", "project", "private", owner_type="user")
        self.assertEqual(result["id"], 8)
        self.assertEqual([x[1] for x in transport.calls], ["GET", "POST"])

    def test_github_organization_repository_creation_uses_org_endpoint(self):
        repo = "https://api.github.com/repos/research-org/project"
        create = "https://api.github.com/orgs/research-org/repos"
        transport = FakeTransport({
            ("GET", repo): (404, {"message": "not found"}),
            ("POST", create): (201, {"id": 9, "private": True}),
        })
        adapter = GitHubAdapter(ApiClient("https://api.github.com", "token", transport))
        result = adapter.ensure_repository("research-org", "project", "private", owner_type="organization")
        self.assertEqual(result["id"], 9)
        self.assertEqual([x[1] for x in transport.calls], ["GET", "POST"])

    def test_existing_github_repository_is_not_mutated_twice(self):
        base = "https://api.github.com/repos/a/b"
        transport = FakeTransport({("GET", base): (200, {"private": True, "id": 7})})
        adapter = GitHubAdapter(ApiClient("https://api.github.com", "token", transport))
        adapter.ensure_repository("a", "b", "private")
        adapter.ensure_repository("a", "b", "private")
        self.assertEqual([x[1] for x in transport.calls], ["GET", "GET"])

    def test_github_permission_failure_is_sanitized_and_reported(self):
        base = "https://api.github.com/repos/a/b"
        transport = FakeTransport({("GET", base): (200, {"private": True}), ("PATCH", base): (403, {"message": "sensitive"})})
        adapter = GitHubAdapter(ApiClient("https://api.github.com", "token", transport))
        with self.assertRaises(ProviderError) as caught:
            adapter.ensure_repository("a", "b", "public", {"allowed": True, "approvalId": "approved"})
        self.assertEqual(caught.exception.status, 403)
        self.assertNotIn("sensitive", str(caught.exception))

    def test_public_github_transition_requires_explicit_approval(self):
        base = "https://api.github.com/repos/a/b"
        transport = FakeTransport({("GET", base): (200, {"private": True})})
        adapter = GitHubAdapter(ApiClient("https://api.github.com", "token", transport))
        with self.assertRaisesRegex(ProviderError, "PUBLICATION_APPROVAL_REQUIRED"):
            adapter.ensure_repository("a", "b", "public")
        self.assertEqual([x[1] for x in transport.calls], ["GET"])

    def test_workers_inventory_reads_before_missing_worker_failure(self):
        base = "https://api.cloudflare.com/client/v4/accounts/acct/workers/workers"
        transport = FakeTransport({("GET", base): (200, {"success": True, "result": [{"id": "worker-id-1", "name": "one"}]})})
        adapter = WorkersAdapter(ApiClient("https://api.cloudflare.com/client/v4", "token", transport), "acct")
        self.assertIsNone(adapter.read_worker("missing"))
        self.assertEqual(len(transport.calls), 1)

    def test_missing_worker_is_created_with_private_preview_defaults(self):
        inventory = "https://api.cloudflare.com/client/v4/accounts/acct/workers/workers"
        create = inventory
        transport = FakeTransport({
            ("GET", inventory): (200, {"success": True, "result": []}),
            ("POST", create): (200, {"success": True, "result": {
                "id": "worker-id-1", "name": "new-worker",
                "subdomain": {"enabled": True, "previews_enabled": False},
            }}),
        })
        adapter = WorkersAdapter(ApiClient("https://api.cloudflare.com/client/v4", "token", transport), "acct")
        result = adapter.ensure_worker("new-worker")
        self.assertEqual(result["name"], "new-worker")
        self.assertEqual([x[1] for x in transport.calls], ["GET", "POST"])
        self.assertFalse(transport.calls[-1][3]["subdomain"]["previews_enabled"])

    def test_build_config_is_idempotent(self):
        path = "https://api.cloudflare.com/client/v4/accounts/acct/builds/workers/tag"
        config = {"build_command": "make build", "root_directory": ""}
        transport = FakeTransport({("GET", path): (200, {"success": True, "result": config})})
        adapter = WorkersBuildsAdapter(ApiClient("https://api.cloudflare.com/client/v4", "token", transport), "acct")
        self.assertEqual(adapter.ensure_config("tag", config), config)
        self.assertEqual([x[1] for x in transport.calls], ["GET"])

    def test_trigger_reuses_exact_existing_trigger(self):
        path = "https://api.cloudflare.com/client/v4/accounts/acct/builds/workers/tag/triggers"
        trigger = {"trigger_name": "Production", "branch_includes": ["main"], "build_command": "make build"}
        transport = FakeTransport({("GET", path): (200, {"success": True, "result": [trigger]})})
        adapter = WorkersBuildsAdapter(ApiClient("https://api.cloudflare.com/client/v4", "token", transport), "acct")
        self.assertEqual(adapter.ensure_trigger("tag", trigger), trigger)
        self.assertEqual([x[1] for x in transport.calls], ["GET"])

    def test_trigger_branch_drift_creates_only_after_actual_read(self):
        path = "https://api.cloudflare.com/client/v4/accounts/acct/builds/workers/tag/triggers"
        create = "https://api.cloudflare.com/client/v4/accounts/acct/builds/triggers"
        trigger = {"trigger_name": "Production", "branch_includes": ["main"], "build_command": "make build"}
        old = {"trigger_name": "Production", "branch_includes": ["release"], "build_command": "make build"}
        transport = FakeTransport({
            ("GET", path): (200, {"success": True, "result": [old]}),
            ("POST", create): (200, {"success": True, "result": trigger}),
        })
        adapter = WorkersBuildsAdapter(ApiClient("https://api.cloudflare.com/client/v4", "token", transport), "acct")
        adapter.ensure_trigger("tag", trigger)
        self.assertEqual([x[1] for x in transport.calls], ["GET", "POST"])

    def test_account_access_is_read_only_from_project_apply_surface(self):
        client = ApiClient("https://api.cloudflare.com/client/v4", "token", FakeTransport({}))
        adapter = AccessAdapter(client, "acct")
        with self.assertRaisesRegex(ProviderError, "ACCOUNT_SECURITY_UI_APPROVAL_REQUIRED"):
            adapter.create_account_baseline({"include": []})

    def test_public_production_bypass_uses_exact_hostname_destination(self):
        self.assertEqual(AccessAdapter.public_production_destination("inquirystack.example.workers.dev"),
                         {"type": "public", "uri": "inquirystack.example.workers.dev"})

    def test_public_production_exception_reuses_matching_existing_public_policy(self):
        path = "https://api.cloudflare.com/client/v4/accounts/acct/access/apps"
        app = {"id": "app-1", "name": "manual exception",
               "destinations": [{"type": "public", "uri": "prod.example.workers.dev"}],
               "policies": [{"decision": "bypass"}]}
        transport = FakeTransport({("GET", path): (200, {"success": True, "result": [app]})})
        adapter = AccessAdapter(ApiClient("https://api.cloudflare.com/client/v4", "token", transport), "acct")
        result = adapter.reconcile_worker_visibility("worker", "prod.example.workers.dev", "public",
                                                     {"allowed": True, "approvalId": "site-approval"})
        self.assertEqual(result, app)
        self.assertEqual([x[1] for x in transport.calls], ["GET"])

    def test_public_exception_conflict_blocks_instead_of_overwriting_policy(self):
        path = "https://api.cloudflare.com/client/v4/accounts/acct/access/apps"
        app = {"id": "app-1", "name": "manual policy",
               "destinations": [{"type": "public", "uri": "prod.example.workers.dev"}],
               "policies": [{"decision": "allow"}]}
        transport = FakeTransport({("GET", path): (200, {"success": True, "result": [app]})})
        adapter = AccessAdapter(ApiClient("https://api.cloudflare.com/client/v4", "token", transport), "acct")
        with self.assertRaisesRegex(ProviderError, "ACCESS_APP_CONFLICT"):
            adapter.reconcile_worker_visibility("worker", "prod.example.workers.dev", "public",
                                                 {"allowed": True, "approvalId": "site-approval"})
        self.assertEqual([x[1] for x in transport.calls], ["GET"])


if __name__ == "__main__":
    unittest.main()

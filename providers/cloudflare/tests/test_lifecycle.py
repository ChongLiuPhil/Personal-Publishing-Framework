import importlib.util
import json
from unittest.mock import patch
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "ppf_cloudflare.py"
spec = importlib.util.spec_from_file_location("ppf_cloudflare", SCRIPT)
provider = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provider)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "_site").mkdir()
        (self.root / "cloudflare-builds.yaml").write_text(
            "mode: workers-builds-git\nworker:\n  name: sample\n  static_assets_directory: ./_site\n"
            "platform_security:\n  worker_access:\n    baseline: account-wide\n    destination: all_workers\n    private_by_default: true\n    public_exception: worker-scoped-bypass\n    previews_protected_by_default: true\n    bootstrap_required_before_worker_creation: true\n"
            "commands:\n  deploy: npx wrangler deploy\n", encoding="utf-8")
        (self.root / "publishing.yaml").write_text(
            "publication:\n  web:\n    visibility: restricted\n    access:\n      mode: authenticated\n"
            "deployment:\n  web:\n    production_url: https://example.workers.dev/\n",
            encoding="utf-8")
        (self.root / "wrangler.jsonc").write_text(
            json.dumps({"name": "sample", "assets": {"directory": "./_site"}}), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_restricted_contract(self):
        build, publishing, worker, output = provider.load_contract(self.root)
        self.assertEqual(worker["name"], "sample")
        self.assertTrue(output.is_dir())

    def test_missing_account_access_baseline_fails_closed(self):
        path = self.root / "cloudflare-builds.yaml"
        path.write_text("mode: workers-builds-git\nworker:\n  name: sample\n  static_assets_directory: ./_site\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "account-wide private-by-default Access baseline"):
            provider.load_contract(self.root)

    def test_reference_previews_are_private_and_require_access_verification(self):
        contract = Path(__file__).parents[3] / "templates/quarto-book/cloudflare-builds.yaml"
        policy = provider.yaml.safe_load(contract.read_text(encoding="utf-8"))
        self.assertTrue(policy["git"]["non_production_branch_builds"])
        self.assertTrue(policy["preview"]["enabled_by_default"])
        self.assertIn("account-wide-access-verified", policy["preview"]["enable_only_after"])
        self.assertNotIn("shared-password", policy["access_modes"])

    def test_application_password_mode_is_not_a_publishing_access_mode(self):
        (self.root / "publishing.yaml").write_text(
            "publication:\n  web:\n    visibility: restricted\n    access:\n      mode: shared-password\n",
            encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "explicit access mode"):
            provider.load_contract(self.root)

    def test_mismatched_worker_fails_closed(self):
        (self.root / "wrangler.jsonc").write_text(
            json.dumps({"name": "other", "assets": {"directory": "./_site"}}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "worker.name"):
            provider.load_contract(self.root)

    def test_public_without_open_access_fails_closed(self):
        (self.root / "publishing.yaml").write_text(
            "publication:\n  web:\n    visibility: public\n    access:\n      mode: authenticated\n",
            encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "public publication"):
            provider.load_contract(self.root)

    def test_plan_is_non_mutating_and_keeps_preview_flag_off(self):
        (self.root / "publishing.yaml").write_text(
            "publication:\n  web:\n    visibility: public\n    access:\n      mode: none\n",
            encoding="utf-8")
        self.assertEqual(provider.plan(self.root), 0)
        self.assertFalse((self.root / ".ppf").exists())

    def test_apply_without_provider_credential_makes_no_change(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(provider.apply(self.root), 2)

    def test_rollback_requires_explicit_version_uuid(self):
        self.assertEqual(provider.rollback("latest", self.root), 2)

    def test_rollback_only_allows_previously_verified_version(self):
        (self.root / ".ppf").mkdir()
        version = "11111111-2222-4333-8444-555555555555"
        (self.root / ".ppf/cloudflare-deployment.json").write_text(
            json.dumps({"worker": "sample", "verified_version_ids": [version]}), encoding="utf-8")
        with patch.dict("os.environ", {"CLOUDFLARE_API_TOKEN": "test-token", "CLOUDFLARE_ACCOUNT_ID": "test-account"}):
            with patch.object(provider.subprocess, "run") as run:
                run.return_value.returncode = 0
                self.assertEqual(provider.rollback(version, self.root), 0)
                run.assert_called_once()
                self.assertIn(version, run.call_args.args[0])

    def test_rollback_cannot_cross_worker_boundary(self):
        (self.root / ".ppf").mkdir()
        version = "11111111-2222-4333-8444-555555555555"
        (self.root / ".ppf/cloudflare-deployment.json").write_text(
            json.dumps({"worker": "another-worker", "verified_version_ids": [version]}), encoding="utf-8")
        with patch.dict("os.environ", {"CLOUDFLARE_API_TOKEN": "test-token", "CLOUDFLARE_ACCOUNT_ID": "a" * 32}):
            with patch.object(provider.subprocess, "run") as run:
                self.assertEqual(provider.rollback(version, self.root), 2)
                run.assert_not_called()

    def test_verify_records_real_http_status(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def geturl(self):
                return "https://example.workers.dev/"

        with patch.dict("os.environ", {}, clear=True):
            with patch.object(provider.urllib.request, "urlopen", return_value=Response()):
                self.assertEqual(provider.verify("https://example.workers.dev/", self.root), 0)
        record = json.loads((self.root / ".ppf/cloudflare-deployment.json").read_text())
        self.assertEqual(record["http_status"], 200)
        self.assertEqual(record["result"], "PASS")

    def test_verify_rejects_unrelated_origin_before_request(self):
        with patch.object(provider.urllib.request, "urlopen") as open_url:
            self.assertEqual(provider.verify("https://attacker.example/health", self.root), 2)
        open_url.assert_not_called()
        self.assertFalse((self.root / ".ppf").exists())

    def test_verify_rejects_cross_origin_redirect_without_recording_version(self):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def geturl(self):
                return "https://attacker.example/health"

        with patch.object(provider.urllib.request, "urlopen", return_value=Response()):
            self.assertEqual(provider.verify("https://example.workers.dev/", self.root), 1)
        self.assertFalse((self.root / ".ppf").exists())


if __name__ == "__main__":
    unittest.main()

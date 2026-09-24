import importlib.util
import base64
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
            "commands:\n  deploy: wrangler deploy\ntoolchain:\n  wrangler: 4.135.0\n", encoding="utf-8")
        (self.root / "publishing.yaml").write_text(
            "publication:\n  web:\n    visibility: restricted\n    access:\n      mode: authenticated\n"
            "deployment:\n  web:\n    production_url: https://example.workers.dev/\n",
            encoding="utf-8")
        (self.root / "wrangler.jsonc").write_text(
            json.dumps({"name": "sample", "assets": {"directory": "./_site"}}), encoding="utf-8")
        (self.root / "package.json").write_text(
            json.dumps({"devDependencies": {"wrangler": "4.135.0"}, "scripts": {"cloudflare:deploy": "wrangler deploy"}}), encoding="utf-8")
        (self.root / "package-lock.json").write_text(json.dumps({"packages": {
            "": {"devDependencies": {"wrangler": "4.135.0"}},
            "node_modules/wrangler": {
                "version": "4.135.0",
                "resolved": "https://registry.npmjs.org/wrangler/-/wrangler-4.135.0.tgz",
                "integrity": "sha512-" + base64.b64encode(b"x" * 64).decode("ascii"),
            },
        }}), encoding="utf-8")
        entrypoint = self.root / "node_modules/wrangler/bin/wrangler.js"
        entrypoint.parent.mkdir(parents=True)
        entrypoint.write_text("// pinned Wrangler fixture\n", encoding="utf-8")
        (entrypoint.parent.parent / "package.json").write_text(json.dumps({"version": "4.135.0"}), encoding="utf-8")

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

    def test_reference_previews_are_disabled_until_access_verification(self):
        contract = Path(__file__).parents[3] / "templates/quarto-book/cloudflare-builds.yaml"
        policy = provider.yaml.safe_load(contract.read_text(encoding="utf-8"))
        self.assertFalse(policy["git"]["non_production_branch_builds"])
        self.assertFalse(policy["preview"]["enabled_by_default"])
        self.assertIn("access-protection-verified", policy["preview"]["enable_only_after"])
        self.assertIn("preview-anonymous-denial-verified", policy["preview"]["enable_only_after"])
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

    def test_apply_rejects_repository_configured_arbitrary_command(self):
        path = self.root / "cloudflare-builds.yaml"
        path.write_text(path.read_text(encoding="utf-8").replace("deploy: wrangler deploy", "deploy: python -c print-secret"), encoding="utf-8")
        with patch.dict("os.environ", {"CLOUDFLARE_API_TOKEN": "test-token", "CLOUDFLARE_ACCOUNT_ID": "test-account"}):
            with patch.object(provider.subprocess, "run") as run:
                self.assertEqual(provider.apply(self.root), 2)
                run.assert_not_called()

    def test_apply_rejects_unpinned_wrangler_package_source(self):
        path = self.root / "package-lock.json"
        lock = json.loads(path.read_text(encoding="utf-8"))
        lock["packages"]["node_modules/wrangler"]["resolved"] = "https://attacker.example/wrangler.tgz"
        path.write_text(json.dumps(lock), encoding="utf-8")
        with patch.dict("os.environ", {"CLOUDFLARE_API_TOKEN": "test-token", "CLOUDFLARE_ACCOUNT_ID": "test-account"}):
            with patch.object(provider.shutil, "which", return_value="/usr/bin/node"):
                with patch.object(provider.subprocess, "run") as run:
                    self.assertEqual(provider.apply(self.root), 2)
                    run.assert_not_called()

    def test_apply_runs_only_pinned_wrangler_with_minimal_environment(self):
        package_path = self.root / "package.json"
        package = json.loads(package_path.read_text(encoding="utf-8"))
        package["scripts"]["cloudflare:deploy"] = "python -c print-secret"
        package_path.write_text(json.dumps(package), encoding="utf-8")
        with patch.dict("os.environ", {
            "CLOUDFLARE_API_TOKEN": "test-token",
            "CLOUDFLARE_ACCOUNT_ID": "test-account",
            "GITHUB_TOKEN": "must-not-be-inherited",
            "AWS_SECRET_ACCESS_KEY": "must-not-be-inherited",
        }, clear=True):
            with patch.object(provider.shutil, "which", return_value="/usr/bin/node"):
                with patch.object(provider.subprocess, "run") as run:
                    run.return_value.returncode = 0
                    self.assertEqual(provider.apply(self.root), 0)
        command = run.call_args.args[0]
        env = run.call_args.kwargs["env"]
        self.assertEqual(command[0], "/usr/bin/node")
        self.assertEqual(command[1], str((self.root / "node_modules/wrangler/bin/wrangler.js").resolve()))
        self.assertEqual(command[2:], ["deploy"])
        self.assertEqual(env["CLOUDFLARE_API_TOKEN"], "test-token")
        self.assertEqual(env["CLOUDFLARE_ACCOUNT_ID"], "test-account")
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", env)
        self.assertEqual(run.call_args.kwargs["stdout"], provider.subprocess.PIPE)
        self.assertEqual(run.call_args.kwargs["stderr"], provider.subprocess.PIPE)

    def test_rollback_requires_explicit_version_uuid(self):
        self.assertEqual(provider.rollback("latest", self.root), 2)

    def test_rollback_only_allows_previously_verified_version(self):
        (self.root / ".ppf").mkdir()
        version = "11111111-2222-4333-8444-555555555555"
        (self.root / ".ppf/cloudflare-deployment.json").write_text(
            json.dumps({"worker": "sample", "verified_version_ids": [version]}), encoding="utf-8")
        with patch.dict("os.environ", {"CLOUDFLARE_API_TOKEN": "test-token", "CLOUDFLARE_ACCOUNT_ID": "test-account"}):
            with patch.object(provider.shutil, "which", return_value="/usr/bin/node"):
                with patch.object(provider.subprocess, "run") as run:
                    run.return_value.returncode = 0
                    self.assertEqual(provider.rollback(version, self.root), 0)
                    run.assert_called_once()
                    self.assertIn(version, run.call_args.args[0])
                    self.assertNotIn("GITHUB_TOKEN", run.call_args.kwargs["env"])

    def test_rollback_cannot_cross_worker_boundary(self):
        (self.root / ".ppf").mkdir()
        version = "11111111-2222-4333-8444-555555555555"
        (self.root / ".ppf/cloudflare-deployment.json").write_text(
            json.dumps({"worker": "another-worker", "verified_version_ids": [version]}), encoding="utf-8")
        with patch.dict("os.environ", {"CLOUDFLARE_API_TOKEN": "test-token", "CLOUDFLARE_ACCOUNT_ID": "a" * 32}):
            with patch.object(provider.subprocess, "run") as run:
                self.assertEqual(provider.rollback(version, self.root), 2)
                run.assert_not_called()

    def test_verify_records_restricted_anonymous_denial_as_success(self):
        probe = {
            "status": 403,
            "final_url": "https://example.workers.dev/",
            "location": "",
        }
        with patch.dict("os.environ", {}, clear=True):
            with patch.object(provider, "_anonymous_probe", return_value=probe):
                self.assertEqual(provider.verify("https://example.workers.dev/", self.root), 0)
        record = json.loads((self.root / ".ppf/cloudflare-deployment.json").read_text())
        self.assertEqual(record["http_status"], 403)
        self.assertEqual(record["result"], "PASS")
        self.assertTrue(record["anonymous_denied"])
        self.assertEqual(record["expected_anonymous_behavior"], "anonymous-denied-or-challenged")

    def test_public_verify_requires_http_success(self):
        (self.root / "publishing.yaml").write_text(
            "publication:\n  web:\n    visibility: public\n    access:\n      mode: none\n"
            "deployment:\n  web:\n    production_url: https://example.workers.dev/\n",
            encoding="utf-8",
        )
        probe = {
            "status": 200,
            "final_url": "https://example.workers.dev/",
            "location": "",
        }
        with patch.dict("os.environ", {}, clear=True):
            with patch.object(provider, "_anonymous_probe", return_value=probe):
                self.assertEqual(provider.verify("https://example.workers.dev/", self.root), 0)
        record = json.loads((self.root / ".ppf/cloudflare-deployment.json").read_text())
        self.assertFalse(record["anonymous_denied"])
        self.assertEqual(record["expected_anonymous_behavior"], "anonymous-success")


    def test_verify_rejects_unrelated_origin_before_request(self):
        with patch.object(provider, "_anonymous_probe") as probe:
            self.assertEqual(provider.verify("https://attacker.example/health", self.root), 2)
        probe.assert_not_called()
        self.assertFalse((self.root / ".ppf").exists())

    def test_verify_rejects_cross_origin_public_redirect_without_recording_version(self):
        (self.root / "publishing.yaml").write_text(
            "publication:\n  web:\n    visibility: public\n    access:\n      mode: none\n"
            "deployment:\n  web:\n    production_url: https://example.workers.dev/\n",
            encoding="utf-8",
        )
        probe = {
            "status": 200,
            "final_url": "https://attacker.example/health",
            "location": "",
        }
        with patch.object(provider, "_anonymous_probe", return_value=probe):
            self.assertEqual(provider.verify("https://example.workers.dev/", self.root), 1)
        self.assertFalse((self.root / ".ppf").exists())

    def test_restricted_access_login_redirect_counts_as_denied(self):
        probe = {
            "status": 302,
            "final_url": "https://example.workers.dev/",
            "location": "https://example.cloudflareaccess.com/cdn-cgi/access/login/example",
        }
        with patch.object(provider, "_anonymous_probe", return_value=probe):
            self.assertEqual(provider.verify("https://example.workers.dev/", self.root), 0)
        record = json.loads((self.root / ".ppf/cloudflare-deployment.json").read_text())
        self.assertTrue(record["anonymous_denied"])



if __name__ == "__main__":
    unittest.main()

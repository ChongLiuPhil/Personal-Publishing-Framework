import copy
import json
from pathlib import Path
import tempfile
import unittest

from providers.infrastructure.manifest import REPO_ROOT, load_manifest


TEMPLATE = REPO_ROOT / "templates/quarto-book/project.infrastructure.json"


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.base = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def test_reference_template_is_valid_and_private_by_default(self):
        manifest = load_manifest(TEMPLATE)
        self.assertEqual(manifest["github"]["repositoryVisibility"], "private")
        self.assertEqual(manifest["cloudflare"]["applicationVisibility"], "private")
        self.assertEqual(manifest["cloudflare"]["previewVisibility"], "private")
        self.assertFalse(manifest["cloudflare"]["publicBypass"])
        self.assertFalse(manifest["policy"]["paidServicesAllowed"])
        self.assertEqual(manifest["schemaVersion"], 2)
        self.assertEqual(manifest["cloudflare"]["accessMode"], "worker-scoped-access")
        self.assertEqual(manifest["deployment"]["provider"], "cloudflare-workers-builds")
        self.assertEqual(manifest["deployment"]["securityProfile"], "workers-builds-native")
        self.assertEqual(manifest["deployment"]["credentialStrategy"], "provider-managed-user-token")
        self.assertFalse(manifest["deployment"]["secretBroker"])
        self.assertFalse(manifest["deployment"]["previewDeployments"])

    def test_external_ci_rejects_broader_or_mismatched_credential_profile(self):
        item = copy.deepcopy(self.base)
        item["deployment"].update(
            provider="github-actions-cloudflare-workers",
            securityProfile="agent-provisioned-external-ci",
            credentialStrategy="provider-managed-user-token",
            secretBroker=True,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.infrastructure.json"
            path.write_text(json.dumps(item), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_manifest(path)

    def test_two_visibility_dimensions_are_independent(self):
        cases = [
            ("private", "private", False),
            ("private", "public", False),
            ("public", "private", True),
            ("public", "public", True),
        ]
        for repository_visibility, app_visibility, open_source in cases:
            with self.subTest(repository=repository_visibility, app=app_visibility):
                item = copy.deepcopy(self.base)
                item["github"]["repositoryVisibility"] = repository_visibility
                item["cloudflare"]["applicationVisibility"] = app_visibility
                item["cloudflare"]["publicBypass"] = False
                item["release"]["state"] = "public" if repository_visibility == "public" or app_visibility == "public" else "private"
                item["release"]["openSource"] = open_source
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "project.infrastructure.json"
                    path.write_text(json.dumps(item), encoding="utf-8")
                    self.assertEqual(load_manifest(path), item)

    def test_public_repository_does_not_automatically_make_app_public(self):
        item = copy.deepcopy(self.base)
        item["github"]["repositoryVisibility"] = "public"
        item["release"] = {"state": "public", "openSource": True}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.infrastructure.json"
            path.write_text(json.dumps(item), encoding="utf-8")
            self.assertEqual(load_manifest(path)["cloudflare"]["applicationVisibility"], "private")

    def test_public_app_requires_worker_bypass_under_account_wide_access(self):
        item = copy.deepcopy(self.base)
        item["cloudflare"]["accessMode"] = "account-wide-access"
        item["cloudflare"]["applicationVisibility"] = "public"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.infrastructure.json"
            path.write_text(json.dumps(item), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "public bypass"):
                load_manifest(path)

    def test_worker_scoped_access_rejects_account_wide_public_bypass(self):
        item = copy.deepcopy(self.base)
        item["cloudflare"]["publicBypass"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.infrastructure.json"
            path.write_text(json.dumps(item), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "worker-scoped Access"):
                load_manifest(path)

    def test_worker_slug_and_build_branch_must_match_project(self):
        item = copy.deepcopy(self.base)
        item["cloudflare"]["worker"] = "other-worker"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.infrastructure.json"
            path.write_text(json.dumps(item), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "cloudflare.worker"):
                load_manifest(path)

    def test_public_repository_requires_open_source_release(self):
        item = copy.deepcopy(self.base)
        item["github"]["repositoryVisibility"] = "public"
        item["release"]["state"] = "public"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.infrastructure.json"
            path.write_text(json.dumps(item), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "openSource"):
                load_manifest(path)


if __name__ == "__main__":
    unittest.main()

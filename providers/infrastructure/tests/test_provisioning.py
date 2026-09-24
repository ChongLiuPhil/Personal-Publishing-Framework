import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

from providers.infrastructure.manifest import REPO_ROOT
from providers.infrastructure.provisioning import ProjectProvisioner


TEMPLATE = REPO_ROOT / "templates/quarto-book/project.infrastructure.json"


class FakeGitHub:
    def __init__(self, repo=None, secrets=None):
        self.repo = repo
        self.secrets = secrets or {"CLOUDFLARE_API_TOKEN": False, "CLOUDFLARE_ACCOUNT_ID": False}
        self.created = 0

    def read_repository(self, owner, repository):
        return self.repo

    def ensure_repository(self, owner, repository, visibility, approval=None, owner_type="user"):
        self.created += 1
        self.repo = {"id": 123, "private": True, "name": repository, "owner_type": owner_type}
        return self.repo

    def deployment_secret_status(self, owner, repository):
        return dict(self.secrets)


class FakeWorkers:
    def __init__(self, worker=None):
        self.worker = worker
        self.created = 0

    def read_worker(self, name):
        return self.worker

    def ensure_worker(self, name):
        self.created += 1
        self.worker = {"id": "worker-id-1", "name": name}
        return self.worker


class FakeAccess:
    def __init__(self, enabled=True):
        self.enabled = enabled

    def account_baseline(self):
        return {"id": "access-app-1"} if self.enabled else None


class ProvisioningTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def test_platform_access_baseline_blocks_before_mutation(self):
        github = FakeGitHub()
        workers = FakeWorkers()
        result = ProjectProvisioner(github, workers, FakeAccess(False)).apply(self.manifest)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["blocker"], "ACCOUNT_WIDE_ACCESS_NOT_VERIFIED")
        self.assertEqual(github.created, 0)
        self.assertEqual(workers.created, 0)

    def test_apply_creates_private_repo_and_worker_then_requests_broker(self):
        github = FakeGitHub()
        workers = FakeWorkers()
        result = ProjectProvisioner(github, workers, FakeAccess(True)).apply(self.manifest)
        self.assertEqual(result["status"], "SECRET_BROKER_REQUIRED")
        self.assertEqual(github.created, 1)
        self.assertEqual(workers.created, 1)
        request = result["secretBrokerRequest"]
        self.assertEqual(request["credential"]["scope"], "individual-worker")
        self.assertEqual(request["credential"]["role"], "Editor")
        self.assertTrue(request["rules"]["plaintextMustNotEnterModelContext"])
        self.assertNotIn("value", json.dumps(request).lower())
        schema = json.loads((REPO_ROOT / "schema/secret-broker-request.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(request)), [])

    def test_existing_scoped_credential_is_ready_for_ci(self):
        secrets = {"CLOUDFLARE_API_TOKEN": True, "CLOUDFLARE_ACCOUNT_ID": True}
        github = FakeGitHub({"id": 123, "private": True}, secrets)
        workers = FakeWorkers({"id": "worker-id-1", "name": self.manifest["cloudflare"]["worker"]})
        result = ProjectProvisioner(github, workers, FakeAccess(True)).apply(self.manifest)
        self.assertEqual(result["status"], "READY_FOR_CI")
        self.assertEqual(github.created, 0)
        self.assertEqual(workers.created, 0)

    def test_public_new_project_is_not_silently_provisioned(self):
        item = copy.deepcopy(self.manifest)
        item["github"]["repositoryVisibility"] = "public"
        item["release"] = {"state": "public", "openSource": True}
        result = ProjectProvisioner(FakeGitHub(), FakeWorkers(), FakeAccess(True)).apply(item)
        self.assertEqual(result["blocker"], "NEW_PROJECT_REPOSITORY_MUST_START_PRIVATE")


if __name__ == "__main__":
    unittest.main()

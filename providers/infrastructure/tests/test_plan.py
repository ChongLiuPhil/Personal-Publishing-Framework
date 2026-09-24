import copy
import json
from pathlib import Path
import unittest

from providers.infrastructure.manifest import REPO_ROOT
from providers.infrastructure.plan import plan_reconciliation


TEMPLATE = REPO_ROOT / "templates/quarto-book/project.infrastructure.json"
GATE = {
    "allowed": True,
    "approvalId": "approval-example-1",
    "checks": {
        "contentReady": True,
        "licenseReady": True,
        "privacyReady": True,
        "secretAuditReady": True,
    },
}


def actual_state():
    return {
        "github": {"repositoryExists": True, "repositoryId": "123", "repositoryVisibility": "private", "deploymentSecrets": {"CLOUDFLARE_API_TOKEN": True, "CLOUDFLARE_ACCOUNT_ID": True}},
        "cloudflare": {
            "workerExists": True,
            "workerId": "sample-worker",
            "workerTag": "worker-tag-uuid",
            "accountWideProtection": False,
            "workerScopedProtection": True,
            "applicationVisibility": "private",
            "previewVisibility": "private",
            "controlPrivateWorkerAnonymousDenied": True,
        },
        "builds": {
            "repositoryConnectionUuid": "repo-connection-uuid",
            "productionTriggerUuid": "production-trigger-uuid",
            "productionBranch": "main",
            "previewTriggerUuid": None,
        },
    }


class ReconciliationPlanTests(unittest.TestCase):
    def setUp(self):
        self.desired = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def test_absent_actual_state_never_blindly_creates_resources(self):
        report = plan_reconciliation(self.desired, None)
        self.assertEqual(report["status"], "READ_REQUIRED")
        self.assertEqual(report["operations"], [])
        self.assertFalse(report["mutationsApplied"])

    def test_existing_matching_private_state_is_idempotent(self):
        report = plan_reconciliation(self.desired, actual_state())
        self.assertEqual(report["status"], "PLAN_READY")
        self.assertEqual(report["operations"], [])

    def test_missing_repository_plans_explicit_private_creation(self):
        actual = actual_state()
        actual["github"] = {"repositoryExists": False}
        report = plan_reconciliation(self.desired, actual)
        create = next(op for op in report["operations"] if op["operation"] == "create-private-repository")
        self.assertIn("private=true", create["reason"])
        self.assertFalse(create["mutating"])

    def test_public_app_does_not_publish_private_repository(self):
        desired = copy.deepcopy(self.desired)
        desired["cloudflare"].update(applicationVisibility="public", publicBypass=False)
        desired["release"]["state"] = "public"
        actual = actual_state()
        report = plan_reconciliation(desired, actual, GATE, GATE)
        self.assertEqual(report["status"], "PLAN_READY")
        self.assertEqual(report["repositoryVisibility"]["desired"], "private")
        self.assertIn("remove-target-worker-access", [op["operation"] for op in report["operations"]])
        self.assertNotIn("make-repository-public", [op["operation"] for op in report["operations"]])

    def test_public_app_requires_control_private_worker_verification(self):
        desired = copy.deepcopy(self.desired)
        desired["cloudflare"].update(applicationVisibility="public", publicBypass=False)
        desired["release"]["state"] = "public"
        actual = actual_state()
        actual["cloudflare"]["controlPrivateWorkerAnonymousDenied"] = False
        report = plan_reconciliation(desired, actual, GATE, GATE)
        self.assertEqual(report["status"], "PERMISSION_REQUIRED")
        self.assertTrue(any("control private Worker" in item for item in report["blockers"]))

    def test_public_app_uses_website_gate_without_changing_repo_visibility(self):
        desired = copy.deepcopy(self.desired)
        desired["cloudflare"].update(applicationVisibility="public", publicBypass=False)
        desired["release"]["state"] = "public"
        report = plan_reconciliation(desired, actual_state(), website_gate={"allowed": True, "approvalId": "web-approval-1"})
        self.assertEqual(report["status"], "PLAN_READY")
        self.assertEqual(report["repositoryVisibility"]["desired"], "private")
        self.assertIn("remove-target-worker-access", [op["operation"] for op in report["operations"]])

    def test_external_ci_missing_project_secret_plans_secret_broker_operation(self):
        desired = copy.deepcopy(self.desired)
        desired["deployment"].update(
            provider="github-actions-cloudflare-workers",
            securityProfile="agent-provisioned-external-ci",
            credentialStrategy="project-scoped-account-token",
            secretBroker=True,
        )
        actual = actual_state()
        actual["github"]["deploymentSecrets"]["CLOUDFLARE_API_TOKEN"] = False
        report = plan_reconciliation(desired, actual)
        self.assertIn(
            "install-project-scoped-deployment-credential",
            [op["operation"] for op in report["operations"]],
        )
        self.assertNotIn(
            "ensure-repository-connection",
            [op["operation"] for op in report["operations"]],
        )

    def test_missing_worker_scoped_access_is_project_gate(self):
        actual = actual_state()
        actual["cloudflare"]["workerScopedProtection"] = False
        report = plan_reconciliation(self.desired, actual)
        self.assertEqual(report["status"], "PERMISSION_REQUIRED")
        self.assertTrue(any("PROJECT_ACCESS_REQUIRED" in item for item in report["blockers"]))
        self.assertIn("protect-target-worker", [op["operation"] for op in report["operations"]])

    def test_account_wide_profile_still_requires_account_baseline(self):
        desired = copy.deepcopy(self.desired)
        desired["cloudflare"]["accessMode"] = "account-wide-access"
        actual = actual_state()
        actual["cloudflare"]["accountWideProtection"] = False
        report = plan_reconciliation(desired, actual)
        self.assertEqual(report["status"], "PERMISSION_REQUIRED")
        self.assertTrue(any("BOOTSTRAP_REQUIRED" in item for item in report["blockers"]))

    def test_public_repository_requires_all_release_checks_and_approval(self):
        desired = copy.deepcopy(self.desired)
        desired["github"]["repositoryVisibility"] = "public"
        desired["release"].update(state="public", openSource=True)
        actual = actual_state()
        blocked = plan_reconciliation(desired, actual, {"allowed": True, "checks": GATE["checks"]})
        self.assertEqual(blocked["status"], "PERMISSION_REQUIRED")
        approved = plan_reconciliation(desired, actual, GATE)
        self.assertIn("make-repository-public", [op["operation"] for op in approved["operations"]])

    def test_public_to_private_is_security_drift_and_warns_about_copies(self):
        actual = actual_state()
        actual["github"]["repositoryVisibility"] = "public"
        report = plan_reconciliation(self.desired, actual)
        self.assertEqual(report["status"], "SECURITY_DRIFT")
        self.assertIn("make-repository-private", [op["operation"] for op in report["operations"]])
        self.assertTrue(report["warnings"])


if __name__ == "__main__":
    unittest.main()

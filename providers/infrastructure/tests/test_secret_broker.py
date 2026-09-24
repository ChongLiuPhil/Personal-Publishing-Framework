import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

from providers.infrastructure.manifest import REPO_ROOT
from providers.infrastructure.secret_broker import (
    ACCOUNT_SECRET,
    TOKEN_SECRET,
    BrokerError,
    MintedCredential,
    TrustedSecretBroker,
)


class FakeIssuer:
    def __init__(self, *, role="Editor", worker_id="worker-id-1", fail=False, revoke_fail=False):
        self.role = role
        self.worker_id = worker_id
        self.fail = fail
        self.revoke_fail = revoke_fail
        self.minted = None
        self.revoked = []

    def mint_worker_editor_token(self, *, worker_id, worker_name, token_name):
        if self.fail:
            raise BrokerError("TOKEN_MINT_FAILED")
        self.minted = MintedCredential(
            token_id="token-id-1",
            worker_id=self.worker_id,
            role=self.role,
            value=bytearray(b"super-secret-token-value"),
        )
        return self.minted

    def revoke_token(self, token_id):
        if self.revoke_fail:
            raise RuntimeError("provider detail that must not escape")
        self.revoked.append(token_id)


class FakeWriter:
    def __init__(self, *, fail_on=None, delete_fail=False, existing=None):
        self.fail_on = fail_on
        self.delete_fail = delete_fail
        self.values = {}
        self.existing = set(existing or [])
        self.deleted = []

    def secret_exists(self, *, owner, repository, name):
        return name in self.existing or name in self.values

    def put_secret(self, *, owner, repository, name, value):
        if self.fail_on == name:
            raise RuntimeError("secret-write-provider-detail")
        self.values[name] = bytes(value)

    def delete_secret(self, *, owner, repository, name):
        if self.delete_fail:
            raise RuntimeError("delete-provider-detail")
        self.values.pop(name, None)
        self.deleted.append(name)


def request():
    return {
        "schema": "ppf/secret-broker-request/v1",
        "provider": "cloudflare",
        "tokenOwner": "account",
        "credential": {
            "scope": "individual-worker",
            "workerId": "worker-id-1",
            "workerName": "project-worker",
            "role": "Editor",
        },
        "target": {
            "provider": "github-actions",
            "repository": "owner/repository",
            "secretNames": [TOKEN_SECRET, ACCOUNT_SECRET],
        },
        "rules": {
            "plaintextMustNotEnterModelContext": True,
            "plaintextMustNotEnterGit": True,
            "discardPlaintextAfterEncryptedWrite": True,
            "existingSecretsMustNotBeOverwritten": True,
            "rollbackMustRevokeMintedToken": True,
        },
    }


class SecretBrokerTests(unittest.TestCase):
    def validate_result(self, result):
        schema = json.loads(
            (REPO_ROOT / "schema/secret-broker-result.schema.json").read_text(encoding="utf-8")
        )
        errors = list(Draft202012Validator(schema).iter_errors(result))
        self.assertEqual(errors, [])

    def test_success_installs_two_secrets_and_returns_no_plaintext(self):
        issuer = FakeIssuer()
        writer = FakeWriter()
        result = TrustedSecretBroker(issuer, writer).execute(
            request(),
            cloudflare_account_id="a" * 32,
        )
        self.assertEqual(result["status"], "INSTALLED")
        self.assertTrue(result["secretMetadataVerified"])
        self.assertFalse(result["plaintextReturned"])
        self.assertEqual(set(result["installedSecretNames"]), {TOKEN_SECRET, ACCOUNT_SECRET})
        self.assertNotIn("super-secret-token-value", json.dumps(result))
        self.assertEqual(writer.values[TOKEN_SECRET], b"super-secret-token-value")
        self.assertEqual(writer.values[ACCOUNT_SECRET], b"a" * 32)
        self.assertTrue(issuer.minted is not None)
        self.assertEqual(bytes(issuer.minted.value), b"\x00" * len(issuer.minted.value))
        self.validate_result(result)

    def test_existing_secret_blocks_before_token_mint(self):
        issuer = FakeIssuer()
        writer = FakeWriter(existing={TOKEN_SECRET})
        result = TrustedSecretBroker(issuer, writer).execute(
            request(),
            cloudflare_account_id="a" * 32,
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["error"], "TARGET_SECRET_ALREADY_EXISTS")
        self.assertIsNone(issuer.minted)
        self.validate_result(result)

    def test_second_write_failure_rolls_back_first_secret_and_token(self):
        issuer = FakeIssuer()
        writer = FakeWriter(fail_on=ACCOUNT_SECRET)
        result = TrustedSecretBroker(issuer, writer).execute(
            request(),
            cloudflare_account_id="a" * 32,
        )
        self.assertEqual(result["status"], "ROLLED_BACK")
        self.assertEqual(result["error"], "SECRET_BROKER_EXECUTION_FAILED")
        self.assertIn(TOKEN_SECRET, writer.deleted)
        self.assertEqual(issuer.revoked, ["token-id-1"])
        self.assertNotIn(TOKEN_SECRET, writer.values)
        self.assertEqual(bytes(issuer.minted.value), b"\x00" * len(issuer.minted.value))
        self.assertNotIn("secret-write-provider-detail", json.dumps(result))
        self.validate_result(result)

    def test_scope_mismatch_revokes_without_writing(self):
        issuer = FakeIssuer(role="Admin")
        writer = FakeWriter()
        result = TrustedSecretBroker(issuer, writer).execute(
            request(),
            cloudflare_account_id="a" * 32,
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["error"], "ISSUER_SCOPE_MISMATCH")
        self.assertEqual(issuer.revoked, ["token-id-1"])
        self.assertEqual(writer.values, {})
        self.validate_result(result)

    def test_incomplete_rollback_is_explicit_and_sanitized(self):
        issuer = FakeIssuer(revoke_fail=True)
        writer = FakeWriter(fail_on=ACCOUNT_SECRET, delete_fail=True)
        result = TrustedSecretBroker(issuer, writer).execute(
            request(),
            cloudflare_account_id="a" * 32,
        )
        self.assertEqual(result["status"], "ROLLBACK_INCOMPLETE")
        self.assertEqual(result["rollbackState"], "incomplete")
        self.assertIn("delete:CLOUDFLARE_API_TOKEN", result["rollbackErrors"])
        self.assertIn("revoke:cloudflare-token", result["rollbackErrors"])
        self.assertNotIn("provider detail", json.dumps(result))
        self.validate_result(result)

    def test_invalid_plaintext_boundary_is_rejected_before_mint(self):
        item = request()
        item["rules"]["plaintextMustNotEnterModelContext"] = False
        issuer = FakeIssuer()
        with self.assertRaisesRegex(BrokerError, "PLAINTEXT_BOUNDARY_NOT_ENFORCED"):
            TrustedSecretBroker(issuer, FakeWriter()).execute(
                item,
                cloudflare_account_id="a" * 32,
            )
        self.assertIsNone(issuer.minted)

    def test_invalid_account_id_blocks_without_mint(self):
        issuer = FakeIssuer()
        result = TrustedSecretBroker(issuer, FakeWriter()).execute(
            request(),
            cloudflare_account_id="not-an-account-id",
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["error"], "INVALID_CLOUDFLARE_ACCOUNT_ID")
        self.assertIsNone(issuer.minted)
        self.validate_result(result)


if __name__ == "__main__":
    unittest.main()

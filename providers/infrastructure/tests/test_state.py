import json
import os
from pathlib import Path
import tempfile
import unittest

from providers.infrastructure.state import IntegrationStateStore


class IntegrationStateTests(unittest.TestCase):
    def test_state_is_atomically_saved_with_private_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            store = IntegrationStateStore(Path(directory) / "private-state")
            state = {"projectId": "sample", "builds": {"buildTokenUuid": "non-secret-uuid"}}
            path = store.write("sample", state)
            self.assertEqual(store.read("sample"), state)
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)
            self.assertEqual(os.stat(path.parent).st_mode & 0o777, 0o700)

    def test_secret_values_are_rejected_before_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            store = IntegrationStateStore(Path(directory) / "private-state")
            with self.assertRaisesRegex(ValueError, "secret-bearing field"):
                store.write("sample", {"projectId": "sample", "apiToken": "must-not-save"})

    def test_bearer_credentials_are_rejected_from_values(self):
        with tempfile.TemporaryDirectory() as directory:
            store = IntegrationStateStore(Path(directory) / "private-state")
            with self.assertRaisesRegex(ValueError, "credential-like value"):
                store.write("sample", {"projectId": "sample", "note": "Bearer abc123"})

    def test_audit_events_are_append_only_jsonl_and_reject_secret_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            store = IntegrationStateStore(Path(directory) / "private-state")
            event = {
                "projectId": "sample",
                "timestamp": "2026-09-23T00:00:00Z",
                "actor": "operator",
                "operation": "DEPLOYMENT_COMPLETED",
                "previousState": {"version": "old"},
                "desiredState": {"version": "new"},
                "actualResult": {"version": "new"},
                "verification": "passed",
                "error": None,
            }
            path = store.append_audit(event)
            store.append_audit(event)
            self.assertEqual([json.loads(line) for line in path.read_text().splitlines()], [event, event])
            with self.assertRaisesRegex(ValueError, "secret-bearing field"):
                store.append_audit({**event, "secret": "no"})


if __name__ == "__main__":
    unittest.main()

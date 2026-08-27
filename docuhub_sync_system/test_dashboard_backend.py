import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from dashboard.backend import app as dashboard_app
from sync_accounting import build_synchronization_report


class DashboardBackendTests(unittest.TestCase):
    def sample_report(self, sync_id="20260827T120000_000000Z", status="completed"):
        return build_synchronization_report(
            sync_id=sync_id,
            mode="dashboard_pipeline",
            started_at="2026-08-27T12:00:00+00:00",
            completed_at="2026-08-27T12:01:30+00:00",
            status=status,
            generation_report={
                "total_artifacts": 12,
                "new_count": 2,
                "updated_count": 3,
                "deleted_count": 1,
            },
            metadata={"completed_steps": ["pull_repository"]},
        )

    def test_synchronization_summary_includes_duration_and_usage(self):
        summary = dashboard_app._synchronization_summary(self.sample_report())
        self.assertEqual(90.0, summary["duration_seconds"])
        self.assertEqual(12, summary["total_artifacts"])
        self.assertEqual("completed", summary["status"])

    def test_history_is_sorted_newest_first(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            older = self.sample_report("older")
            newer = self.sample_report("newer")
            newer["completed_at"] = "2026-08-28T12:00:00+00:00"
            for report in (older, newer):
                with open(os.path.join(temp_dir, f"sync_{report['sync_id']}.json"), "w", encoding="utf-8") as handle:
                    json.dump(report, handle)
            with patch.object(dashboard_app, "SYNCHRONIZATION_HISTORY_DIR", temp_dir):
                history = dashboard_app._load_synchronization_history(limit=10)
            self.assertEqual(["newer", "older"], [item["sync_id"] for item in history])

    def test_pipeline_execution_is_local_only_without_token(self):
        local_request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"), headers={})
        remote_request = SimpleNamespace(client=SimpleNamespace(host="203.0.113.10"), headers={})
        with patch.dict(os.environ, {"DASHBOARD_OPERATOR_TOKEN": ""}, clear=False):
            dashboard_app._require_operator(local_request)
            with self.assertRaises(HTTPException) as context:
                dashboard_app._require_operator(remote_request)
        self.assertEqual(403, context.exception.status_code)

    def test_configured_operator_token_is_required(self):
        request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"), headers={})
        with patch.dict(os.environ, {"DASHBOARD_OPERATOR_TOKEN": "secret"}, clear=False):
            with self.assertRaises(HTTPException) as context:
                dashboard_app._require_operator(request)
            self.assertEqual(401, context.exception.status_code)
            request.headers = {"x-ciroh-operator-key": "secret"}
            dashboard_app._require_operator(request)


if __name__ == "__main__":
    unittest.main()

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

    def test_github_repository_stage_is_opt_in(self):
        default_steps = dashboard_app._dashboard_pipeline_steps(False)
        github_steps = dashboard_app._dashboard_pipeline_steps(True)
        self.assertEqual(6, len(default_steps))
        self.assertEqual(8, len(github_steps))
        self.assertNotIn(
            "generate_github_repository_artifacts",
            [step.key for step in default_steps],
        )
        self.assertIn(
            "generate_github_repository_artifacts",
            [step.key for step in github_steps],
        )
        self.assertIn(
            "update_github_repository_database",
            [step.key for step in github_steps],
        )

    def test_history_is_sorted_newest_first(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            older = self.sample_report("older")
            newer = self.sample_report("newer")
            newer["completed_at"] = "2026-08-28T12:00:00+00:00"
            for report in (older, newer):
                with open(os.path.join(temp_dir, f"sync_{report['sync_id']}.json"), "w", encoding="utf-8") as handle:
                    json.dump(report, handle)
            with tempfile.TemporaryDirectory() as bootstrap_dir, patch.object(
                dashboard_app, "SYNCHRONIZATION_HISTORY_DIR", temp_dir
            ), patch.object(
                dashboard_app,
                "BOOTSTRAP_SYNCHRONIZATION_HISTORY_DIR",
                bootstrap_dir,
            ):
                history = dashboard_app._load_synchronization_history(limit=10)
            self.assertEqual(["newer", "older"], [item["sync_id"] for item in history])

    def test_runtime_history_overrides_and_merges_with_bootstrap(self):
        with tempfile.TemporaryDirectory() as bootstrap_dir, tempfile.TemporaryDirectory() as runtime_dir:
            shared_seed = self.sample_report("shared")
            shared_seed["content"]["total_artifacts"] = 10
            shared_runtime = self.sample_report("shared")
            shared_runtime["content"]["total_artifacts"] = 99
            local = self.sample_report("local")
            local["completed_at"] = "2026-08-29T12:00:00+00:00"
            for directory, report in (
                (bootstrap_dir, shared_seed),
                (runtime_dir, shared_runtime),
                (runtime_dir, local),
            ):
                with open(
                    os.path.join(directory, f"sync_{report['sync_id']}.json"),
                    "w",
                    encoding="utf-8",
                ) as handle:
                    json.dump(report, handle)

            with patch.object(
                dashboard_app,
                "BOOTSTRAP_SYNCHRONIZATION_HISTORY_DIR",
                bootstrap_dir,
            ), patch.object(
                dashboard_app, "SYNCHRONIZATION_HISTORY_DIR", runtime_dir
            ):
                history = dashboard_app._load_synchronization_history(limit=10)
                detail = dashboard_app._load_synchronization_detail("shared")

            self.assertEqual(["local", "shared"], [item["sync_id"] for item in history])
            shared = next(item for item in history if item["sync_id"] == "shared")
            self.assertEqual(99, shared["total_artifacts"])
            self.assertEqual(99, detail["content"]["total_artifacts"])

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

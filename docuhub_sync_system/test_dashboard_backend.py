import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
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

    def test_synchronization_summary_aggregates_optional_sources(self):
        report = self.sample_report()
        report["metadata"].update({
            "github_repositories": {
                "total_artifacts": 4,
                "total_chunks": 8,
                "new_count": 1,
                "updated_count": 2,
                "deleted_count": 1,
            },
            "hydroshare_resources": {
                "total_artifacts": 6,
                "total_chunks": 12,
                "new_count": 2,
                "updated_count": 1,
                "removed_count": 3,
            },
        })

        summary = dashboard_app._synchronization_summary(report)

        self.assertEqual(22, summary["total_artifacts"])
        self.assertEqual(5, summary["new_count"])
        self.assertEqual(6, summary["updated_count"])
        self.assertEqual(5, summary["deleted_count"])

    def test_github_repository_stage_is_opt_in(self):
        default_steps = dashboard_app._dashboard_pipeline_steps(False, False)
        github_steps = dashboard_app._dashboard_pipeline_steps(True, False)
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

    def test_hydroshare_stage_is_opt_in(self):
        hydroshare_steps = dashboard_app._dashboard_pipeline_steps(False, True)
        all_source_steps = dashboard_app._dashboard_pipeline_steps(True, True)

        self.assertEqual(8, len(hydroshare_steps))
        self.assertEqual(10, len(all_source_steps))
        self.assertIn(
            "generate_hydroshare_resources",
            [step.key for step in hydroshare_steps],
        )
        self.assertIn(
            "update_hydroshare_database",
            [step.key for step in hydroshare_steps],
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

    def test_source_status_uses_reports_and_database_mtime(self):
        with tempfile.TemporaryDirectory() as output_dir, tempfile.TemporaryDirectory() as history_dir, tempfile.TemporaryDirectory() as bootstrap_dir:
            generation_path = os.path.join(
                output_dir, "hydroshare_generation_report.json"
            )
            database_path = os.path.join(
                output_dir, "hydroshare_db_update_result.json"
            )
            with open(generation_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "status": "completed",
                        "completed_at": "2026-10-16T18:09:21+00:00",
                        "total_artifacts": 154,
                        "total_chunks": 3312,
                        "new_count": 150,
                        "updated_count": 4,
                        "removed_count": 2,
                    },
                    handle,
                )
            with open(database_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "status": "completed",
                        "upserted_artifacts": 154,
                        "deactivated_artifacts": 2,
                        "chunks_inserted": 3312,
                        "reconciliation": {"unchanged_artifacts": 7},
                    },
                    handle,
                )
            database_mtime = datetime(
                2026, 10, 16, 19, 0, tzinfo=timezone.utc
            ).timestamp()
            os.utime(database_path, (database_mtime, database_mtime))

            with patch.object(
                dashboard_app, "SYNCHRONIZATION_OUTPUT_DIR", output_dir
            ), patch.object(
                dashboard_app, "SYNCHRONIZATION_HISTORY_DIR", history_dir
            ), patch.object(
                dashboard_app,
                "BOOTSTRAP_SYNCHRONIZATION_HISTORY_DIR",
                bootstrap_dir,
            ):
                response = dashboard_app.source_status()

        self.assertEqual(3, response["count"])
        hydroshare = next(
            item for item in response["items"] if item["key"] == "hydroshare"
        )
        self.assertEqual("HydroShare Research Portal", hydroshare["label"])
        self.assertEqual(3, hydroshare["artifact_type_id"])
        self.assertTrue(hydroshare["optional"])
        self.assertEqual("completed", hydroshare["status"])
        self.assertEqual(
            "2026-10-16T19:00:00+00:00", hydroshare["last_synced_at"]
        )
        self.assertEqual(154, hydroshare["artifacts"])
        self.assertEqual(3312, hydroshare["chunks"])
        self.assertEqual(150, hydroshare["new_count"])
        self.assertEqual(4, hydroshare["updated_count"])
        self.assertEqual(2, hydroshare["removed_count"])
        self.assertEqual(154, hydroshare["db_upserted"])
        self.assertEqual(2, hydroshare["db_deactivated"])
        self.assertEqual(7, hydroshare["db_unchanged"])
        self.assertEqual(
            "not_synced",
            next(
                item
                for item in response["items"]
                if item["key"] == "github_repositories"
            )["status"],
        )

    def test_source_status_falls_back_to_latest_history(self):
        with tempfile.TemporaryDirectory() as output_dir, tempfile.TemporaryDirectory() as history_dir, tempfile.TemporaryDirectory() as bootstrap_dir:
            reports = [
                self.sample_report("older"),
                self.sample_report("newer"),
            ]
            reports[1]["completed_at"] = "2026-08-29T12:00:00+00:00"
            reports[1]["content"].update(
                {"total_artifacts": 20, "total_chunks": 40}
            )
            reports[1]["database"] = {
                "upserted_artifacts": 5,
                "deactivated_artifacts": 1,
                "reconciliation": {"unchanged_artifacts": 15},
            }
            for report in reports:
                with open(
                    os.path.join(history_dir, f"sync_{report['sync_id']}.json"),
                    "w",
                    encoding="utf-8",
                ) as handle:
                    json.dump(report, handle)

            with patch.object(
                dashboard_app, "SYNCHRONIZATION_OUTPUT_DIR", output_dir
            ), patch.object(
                dashboard_app, "SYNCHRONIZATION_HISTORY_DIR", history_dir
            ), patch.object(
                dashboard_app,
                "BOOTSTRAP_SYNCHRONIZATION_HISTORY_DIR",
                bootstrap_dir,
            ):
                statuses = dashboard_app._load_source_statuses()

        ciroh_hub = next(item for item in statuses if item["key"] == "ciroh_hub")
        self.assertFalse(ciroh_hub["optional"])
        self.assertEqual(
            "2026-08-29T12:00:00+00:00", ciroh_hub["last_synced_at"]
        )
        self.assertEqual(20, ciroh_hub["artifacts"])
        self.assertEqual(40, ciroh_hub["chunks"])
        self.assertEqual(5, ciroh_hub["db_upserted"])
        self.assertEqual(1, ciroh_hub["db_deactivated"])
        self.assertEqual(15, ciroh_hub["db_unchanged"])

    def test_source_status_handles_invalid_or_missing_reports(self):
        with tempfile.TemporaryDirectory() as output_dir, tempfile.TemporaryDirectory() as history_dir, tempfile.TemporaryDirectory() as bootstrap_dir:
            with open(
                os.path.join(output_dir, "generation_report.json"),
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write("{not valid json")

            with patch.object(
                dashboard_app, "SYNCHRONIZATION_OUTPUT_DIR", output_dir
            ), patch.object(
                dashboard_app, "SYNCHRONIZATION_HISTORY_DIR", history_dir
            ), patch.object(
                dashboard_app,
                "BOOTSTRAP_SYNCHRONIZATION_HISTORY_DIR",
                bootstrap_dir,
            ):
                statuses = dashboard_app._load_source_statuses()

        self.assertEqual(3, len(statuses))
        self.assertTrue(all(item["status"] == "not_synced" for item in statuses))
        self.assertTrue(all(item["last_synced_at"] is None for item in statuses))


if __name__ == "__main__":
    unittest.main()

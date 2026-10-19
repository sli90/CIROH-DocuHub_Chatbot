import json
import tempfile
import unittest
from pathlib import Path

from apply_prepared_sync import (
    _database_command,
    _resolve_hydroshare_removal_policy,
)
from prepared_sync import (
    PreparedSyncError,
    _validate_hydroshare_snapshot,
    create_prepared_bundle,
    resolve_prepared_bundle,
    validate_prepared_bundle,
)


class PreparedSyncTests(unittest.TestCase):
    def test_hydroshare_validation_rejects_unknown_portal_type(self):
        artifacts = [{
            "idArtifact": 1,
            "idArtifactType": 3,
            "Title": "Resource",
            "URL": "https://www.hydroshare.org/resource/example/",
            "artifact_role": "hydroshare_resource",
            "hs_research_portal_types": ["Unknown"],
        }]
        chunks = [{
            "idArtifact": 1,
            "idChunk": 1,
            "chunk_type_name": "Abstract",
        }]

        with self.assertRaisesRegex(PreparedSyncError, "unknown research"):
            _validate_hydroshare_snapshot(artifacts, chunks)

    def test_hydroshare_validation_rejects_unknown_chunk_type(self):
        artifacts = [{
            "idArtifact": 1,
            "idArtifactType": 3,
            "Title": "Resource",
            "URL": "https://www.hydroshare.org/resource/example/",
            "artifact_role": "hydroshare_resource",
            "hs_research_portal_types": ["Datasets"],
        }]
        chunks = [{
            "idArtifact": 1,
            "idChunk": 1,
            "chunk_type_name": "Unknown",
        }]

        with self.assertRaisesRegex(PreparedSyncError, "unknown or missing"):
            _validate_hydroshare_snapshot(artifacts, chunks)

    def _write_generated_files(self, root: Path) -> None:
        formatted = root / "dashboard/formated_files"
        formatted.mkdir(parents=True)
        doc_artifacts = [
            {
                "idArtifact": 1,
                "idArtifactType": 1,
                "Title": "Page",
                "URL": "https://hub.ciroh.org/page/",
                "summary_data": {"summary_text": "Page", "keywords": []},
            }
        ]
        doc_chunks = [
            {"idArtifact": 1, "idChunk": 1, "order": 1, "chunk_text": "Page"}
        ]
        github_artifacts = [
            {
                "idArtifact": 2,
                "idArtifactType": 4,
                "Title": "Repo",
                "URL": "https://github.com/CIROH-UA/repo",
                "summary_data": {"summary_text": "Repo", "keywords": []},
            }
        ]
        github_chunks = [
            {"idArtifact": 2, "idChunk": 2, "order": 1, "chunk_text": "Repo"}
        ]
        hydroshare_artifacts = [
            {
                "idArtifact": 3,
                "idArtifactType": 3,
                "Title": "HydroShare resource",
                "URL": "https://www.hydroshare.org/resource/example/",
                "artifact_role": "hydroshare_resource",
                "hs_research_portal_types": ["Datasets", "Notebooks"],
            }
        ]
        hydroshare_chunks = [
            {
                "idArtifact": 3,
                "idChunk": 3,
                "order": 1,
                "chunk_type_name": "Abstract",
                "chunk_text": "HydroShare resource",
            }
        ]
        payloads = {
            "artifacts.json": doc_artifacts,
            "content_chunks.json": doc_chunks,
            "generation_report.json": {"total_artifacts": 1, "total_chunks": 1},
            "coderepo_artifacts.json": github_artifacts,
            "coderepo_chunks.json": github_chunks,
            "github_repository_generation_report.json": {
                "status": "completed",
                "total_artifacts": 1,
                "total_chunks": 1,
            },
            "hydroshare_artifacts.json": hydroshare_artifacts,
            "hydroshare_chunks.json": hydroshare_chunks,
            "hydroshare_generation_report.json": {
                "status": "completed",
                "total_artifacts": 1,
                "total_chunks": 1,
                "discovery_shrink_guard": {
                    "allow_large_removals": True,
                },
            },
        }
        for name, payload in payloads.items():
            (formatted / name).write_text(
                json.dumps(payload), encoding="utf-8"
            )

    def test_bundle_freezes_and_validates_generated_snapshots(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_generated_files(root)

            bundle = create_prepared_bundle(
                root,
                sync_id="sync-test",
                include_github_repositories=True,
                include_hydroshare_resources=True,
            )
            validated = validate_prepared_bundle(bundle)

            self.assertEqual("sync-test", validated["manifest"]["sync_id"])
            self.assertEqual(1, validated["validation"]["docuhub"]["artifacts"])
            self.assertEqual(
                1, validated["validation"]["github_repositories"]["artifacts"]
            )
            self.assertEqual(
                1, validated["validation"]["hydroshare_resources"]["artifacts"]
            )
            self.assertTrue(
                validated["manifest"]["allow_large_hydroshare_removals"]
            )
            self.assertEqual(bundle, resolve_prepared_bundle(root, None))

    def test_bundle_hash_detects_changes_before_database_apply(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_generated_files(root)
            bundle = create_prepared_bundle(
                root,
                sync_id="sync-test",
                include_github_repositories=True,
            )
            (bundle / "docuhub_artifacts.json").write_text("[]", encoding="utf-8")

            with self.assertRaisesRegex(PreparedSyncError, "changed"):
                validate_prepared_bundle(bundle)

    def test_database_apply_command_uses_idempotent_snapshot_reconciliation(self):
        command = _database_command(
            artifacts=Path("artifacts.json"),
            chunks=Path("chunks.json"),
            artifact_type=1,
            result_file=Path("result.json"),
            require_summaries=True,
            skip_embeddings=False,
        )

        self.assertIn("--reconcile-snapshot-artifact-type", command)
        self.assertNotIn("--deactivate-active-artifact-type", command)
        self.assertIn("--require-summaries", command)

    def test_hydroshare_apply_uses_specialized_reconciliation(self):
        command = _database_command(
            artifacts=Path("hydroshare_artifacts.json"),
            chunks=Path("hydroshare_chunks.json"),
            artifact_type=3,
            result_file=Path("result.json"),
            require_summaries=False,
            skip_embeddings=False,
            reconcile_hydroshare_snapshot=True,
            allow_large_hydroshare_removals=True,
        )

        self.assertIn("--reconcile-hydroshare-snapshot", command)
        self.assertIn("--allow-large-hydroshare-removals", command)
        self.assertNotIn("--reconcile-snapshot-artifact-type", command)

    def test_apply_override_requires_reason_and_records_provenance(self):
        manifest = {
            "include_hydroshare_resources": True,
            "allow_large_hydroshare_removals": False,
        }

        with self.assertRaisesRegex(PreparedSyncError, "reason is required"):
            _resolve_hydroshare_removal_policy(
                manifest,
                apply_override=True,
                override_reason=None,
            )

        policy = _resolve_hydroshare_removal_policy(
            manifest,
            apply_override=True,
            override_reason="Reviewed legacy HTTP URL canonicalization.",
        )

        self.assertTrue(policy["allowed"])
        self.assertEqual("apply_override", policy["source"])
        self.assertEqual(
            "Reviewed legacy HTTP URL canonicalization.",
            policy["reason"],
        )


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from apply_prepared_sync import _database_command
from prepared_sync import (
    PreparedSyncError,
    create_prepared_bundle,
    resolve_prepared_bundle,
    validate_prepared_bundle,
)


class PreparedSyncTests(unittest.TestCase):
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
            )
            validated = validate_prepared_bundle(bundle)

            self.assertEqual("sync-test", validated["manifest"]["sync_id"])
            self.assertEqual(1, validated["validation"]["docuhub"]["artifacts"])
            self.assertEqual(
                1, validated["validation"]["github_repositories"]["artifacts"]
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


if __name__ == "__main__":
    unittest.main()

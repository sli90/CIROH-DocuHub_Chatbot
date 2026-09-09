import unittest
from unittest.mock import MagicMock

from Andres_implementation.database import DatabaseManager
from Andres_implementation.process_delta import (
    _repository_snapshot_fingerprint,
    build_metadata,
    deactivate_artifacts_by_urls,
    insert_chunks,
    reconcile_artifact_snapshot,
    validate_version_history_schema,
)


class FakeDatabase:
    def __init__(self, active_rows=None, chunk_types=None, schema_indexes=None):
        self.active_rows = active_rows or []
        self.chunk_types = chunk_types or []
        self.schema_indexes = schema_indexes or []
        self.queries = []
        self.batches = []

    def execute_query(self, query, params=None, fetch=False):
        self.queries.append((query, params, fetch))
        if "SELECT url, metadata FROM tblartifacts" in query:
            return self.active_rows
        if "SELECT idchunktype, typename FROM tblchunktypes" in query:
            return self.chunk_types
        if "FROM pg_index ind" in query:
            return self.schema_indexes
        if "UPDATE tblartifacts SET" in query and "RETURNING idartifact" in query:
            return [{"idartifact": 1}]
        return []

    def execute_batch(self, query, rows, page_size=100):
        self.batches.append((query, rows, page_size))


def repository_artifact(source_id, name):
    return {
        "idArtifact": source_id,
        "idArtifactType": 4,
        "Title": name,
        "URL": f"https://github.com/CIROH-UA/{name}",
        "full_name": f"CIROH-UA/{name}",
        "artifact_role": "repository",
        "frozen_commit_sha": f"sha-{name}",
        "summary_data": {"summary_text": name, "keywords": [name]},
    }


def repository_chunk(source_id, chunk_id, text="overview"):
    return {
        "idArtifact": source_id,
        "idChunk": chunk_id,
        "idChunkType": None,
        "chunk_type_name": "Project Overview",
        "order": 1,
        "chunk_text": text,
        "idChunkParent": None,
        "section_hint": "Overview",
        "type_specific": {"source_file": "README.md"},
    }


class ProcessDeltaTests(unittest.TestCase):
    def test_schema_validation_rejects_global_url_uniqueness(self):
        db = FakeDatabase(schema_indexes=[{
            "indexname": "tblartifacts_url_key",
            "indexdef": "CREATE UNIQUE INDEX tblartifacts_url_key ON tblartifacts (url)",
            "is_partial": False,
        }])
        with self.assertRaisesRegex(RuntimeError, "global URL uniqueness"):
            validate_version_history_schema(db)

        partial_db = FakeDatabase(schema_indexes=[{
            "indexname": "idx_artifact_url_active",
            "indexdef": "CREATE UNIQUE INDEX idx_artifact_url_active ON tblartifacts (url) WHERE isactive = true",
            "is_partial": True,
        }])
        validate_version_history_schema(partial_db)

    def test_database_session_commits_or_rolls_back_as_one_unit(self):
        manager = DatabaseManager()
        successful_connection = MagicMock()
        manager._conn = successful_connection
        manager.__exit__(None, None, None)
        successful_connection.commit.assert_called_once_with()
        successful_connection.rollback.assert_not_called()
        successful_connection.close.assert_called_once_with()

        failed_connection = MagicMock()
        manager._conn = failed_connection
        manager.__exit__(RuntimeError, RuntimeError("failed"), None)
        failed_connection.rollback.assert_called_once_with()
        failed_connection.commit.assert_not_called()
        failed_connection.close.assert_called_once_with()

    def test_snapshot_reconciliation_leaves_matching_rows_untouched(self):
        first = repository_artifact(1, "first")
        second = repository_artifact(2, "second")
        chunks = [repository_chunk(1, 10), repository_chunk(2, 20)]
        first_fingerprint = _repository_snapshot_fingerprint(first, [chunks[0]])
        db = FakeDatabase(active_rows=[
            {
                "url": first["URL"],
                "metadata": {"sync": {"content_fingerprint": first_fingerprint}},
            },
            {
                "url": "https://github.com/CIROH-UA/removed",
                "metadata": {"sync": {"content_fingerprint": "old"}},
            },
        ])

        upserts, deletes, stats = reconcile_artifact_snapshot(
            db, [first, second], chunks, 4
        )

        self.assertEqual([second["URL"]], [item["URL"] for item in upserts])
        self.assertEqual(
            [{"URL": "https://github.com/CIROH-UA/removed"}], deletes
        )
        self.assertEqual(1, stats["unchanged_artifacts"])
        self.assertEqual(1, stats["missing_or_changed_artifacts"])

    def test_repository_metadata_retains_version_and_fingerprint(self):
        artifact = repository_artifact(1, "sample")
        artifact["_sync_content_fingerprint"] = "fingerprint"
        artifact["description"] = "A sample repository"

        metadata = build_metadata(artifact)

        self.assertEqual(
            "sha-sample", metadata["sync"]["source_version"]
        )
        self.assertEqual(
            "fingerprint", metadata["sync"]["content_fingerprint"]
        )
        self.assertEqual(
            "CIROH-UA/sample", metadata["github_repository"]["full_name"]
        )

    def test_docuhub_metadata_retains_retry_fingerprint(self):
        artifact = {
            "idArtifact": 1,
            "idArtifactType": 1,
            "Title": "Page",
            "URL": "https://hub.ciroh.org/page/",
            "summary_data": {"summary_text": "Page", "keywords": []},
            "_sync_content_fingerprint": "doc-fingerprint",
        }

        metadata = build_metadata(artifact)

        self.assertEqual(
            "doc-fingerprint", metadata["sync"]["content_fingerprint"]
        )

    def test_docuhub_snapshot_retry_is_idempotent_and_tracks_parent_version(self):
        parent = {
            "idArtifact": 1,
            "idArtifactType": 1,
            "Title": "Parent",
            "URL": "https://hub.ciroh.org/parent/",
            "idArtifactParent": None,
            "summary_data": {"summary_text": "Parent", "keywords": []},
        }
        child = {
            "idArtifact": 2,
            "idArtifactType": 1,
            "Title": "Child",
            "URL": "https://hub.ciroh.org/parent/child/",
            "idArtifactParent": 1,
            "summary_data": {"summary_text": "Child", "keywords": []},
        }
        chunks = [
            {"idArtifact": 1, "idChunk": 1, "order": 1, "chunk_text": "p"},
            {"idArtifact": 2, "idChunk": 2, "order": 1, "chunk_text": "c"},
        ]

        first_upserts, _, _ = reconcile_artifact_snapshot(
            FakeDatabase(), [parent, child], chunks, 1
        )
        active_rows = [
            {
                "url": artifact["URL"],
                "metadata": {
                    "sync": {
                        "content_fingerprint": artifact[
                            "_sync_content_fingerprint"
                        ]
                    }
                },
            }
            for artifact in first_upserts
        ]

        retry_upserts, retry_deletes, stats = reconcile_artifact_snapshot(
            FakeDatabase(active_rows=active_rows), [parent, child], chunks, 1
        )

        self.assertEqual([], retry_upserts)
        self.assertEqual([], retry_deletes)
        self.assertEqual(2, stats["unchanged_artifacts"])

        changed_parent = dict(parent, Title="Changed parent")
        changed_upserts, _, _ = reconcile_artifact_snapshot(
            FakeDatabase(active_rows=active_rows),
            [changed_parent, child],
            chunks,
            1,
        )
        self.assertEqual(
            {parent["URL"], child["URL"]},
            {artifact["URL"] for artifact in changed_upserts},
        )

    def test_deactivation_is_type_scoped_and_records_time(self):
        db = FakeDatabase()

        count = deactivate_artifacts_by_urls(db, ["https://example.test/a"], 4)

        self.assertEqual(1, count)
        query, params, fetch = db.queries[0]
        self.assertIn("deactivated_at", query)
        self.assertIn("idartifacttype = %s", query)
        self.assertEqual((["https://example.test/a"], 4), params)
        self.assertTrue(fetch)

    def test_symbolic_chunk_type_is_resolved_by_name(self):
        db = FakeDatabase(
            chunk_types=[{"idchunktype": 21, "typename": "Project Overview"}]
        )
        chunk = repository_chunk(1, 10)

        inserted = insert_chunks(
            db,
            [chunk],
            {1: "https://github.com/CIROH-UA/sample"},
            {"https://github.com/CIROH-UA/sample": 99},
            4,
        )

        self.assertEqual(1, inserted)
        rows = db.batches[0][1]
        self.assertEqual(21, rows[0][1])


if __name__ == "__main__":
    unittest.main()

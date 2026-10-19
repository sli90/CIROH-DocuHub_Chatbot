import unittest
from unittest.mock import MagicMock

from Andres_implementation.database import DatabaseManager
from Andres_implementation.process_delta import (
    _repository_snapshot_fingerprint,
    build_metadata,
    deactivate_artifacts_by_urls,
    ensure_hydroshare_chunk_types,
    ensure_hydroshare_snapshot_portal_mappings,
    get_hydroshare_portal_types,
    insert_hydroshare_portal_mappings,
    insert_chunks,
    parse_date,
    reconcile_artifact_snapshot,
    validate_version_history_schema,
)


class FakeDatabase:
    def __init__(
        self,
        active_rows=None,
        chunk_types=None,
        schema_indexes=None,
        portal_types=None,
        active_artifact_ids=None,
    ):
        self.active_rows = active_rows or []
        self.chunk_types = chunk_types or []
        self.schema_indexes = schema_indexes or []
        self.portal_types = portal_types or []
        self.active_artifact_ids = active_artifact_ids or []
        self.queries = []
        self.batches = []

    def execute_query(self, query, params=None, fetch=False):
        self.queries.append((query, params, fetch))
        if "SELECT url, metadata FROM tblartifacts" in query:
            return self.active_rows
        if "SELECT idchunktype, typename FROM tblchunktypes" in query:
            return self.chunk_types
        if "SELECT idartifact, url FROM tblartifacts" in query:
            return self.active_artifact_ids
        if "FROM tblhsresearchportaltypes;" in query:
            return self.portal_types
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


def hydroshare_artifact(source_id=1, portal_types=None):
    return {
        "idArtifact": source_id,
        "idArtifactType": 3,
        "Title": "HydroShare resource",
        "URL": (
            "https://www.hydroshare.org/resource/"
            "0123456789abcdef0123456789abcdef/"
        ),
        "artifact_role": "hydroshare_resource",
        "resource_id": "0123456789abcdef0123456789abcdef",
        "resource_type": "CompositeResource",
        "date_last_updated": "2026-10-15T12:30:45.123456Z",
        "abstract": "Example resource",
        "hs_research_portal_types": portal_types or ["Datasets"],
        "summary_data": {
            "summary_text": "HydroShare resource",
            "keywords": ["HydroShare"],
        },
    }


def hydroshare_reconciliation_fixture(active_count=20, removal_count=5):
    artifacts = []
    active_rows = []
    retained_count = active_count - removal_count
    for index in range(retained_count):
        resource_id = f"{index + 1:032x}"
        artifact = hydroshare_artifact(source_id=index + 1)
        artifact["resource_id"] = resource_id
        artifact["URL"] = f"https://www.hydroshare.org/resource/{resource_id}/"
        fingerprint = _repository_snapshot_fingerprint(artifact, [])
        artifacts.append(artifact)
        active_rows.append({
            "url": artifact["URL"],
            "metadata": {"sync": {"content_fingerprint": fingerprint}},
        })
    for index in range(removal_count):
        resource_id = f"{active_count + index + 1:032x}"
        active_rows.append({
            "url": f"https://www.hydroshare.org/resource/{resource_id}/",
            "metadata": {"sync": {"content_fingerprint": "old"}},
        })
    return artifacts, active_rows


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

    def test_hydroshare_metadata_date_and_portal_types_are_preserved(self):
        artifact = hydroshare_artifact(
            portal_types=["datasets", "Apps", "Datasets"]
        )
        artifact["_sync_content_fingerprint"] = "hs-fingerprint"

        metadata = build_metadata(artifact)

        self.assertEqual(
            "0123456789abcdef0123456789abcdef",
            metadata["hydroshare"]["resource_id"],
        )
        self.assertEqual(
            ["Apps", "Datasets"],
            metadata["hydroshare"]["hs_research_portal_types"],
        )
        self.assertEqual(
            "2026-10-15T12:30:45.123456Z",
            metadata["sync"]["source_version"],
        )
        self.assertEqual(
            "hs-fingerprint", metadata["sync"]["content_fingerprint"]
        )
        self.assertIsNotNone(parse_date(artifact["date_last_updated"]))

    def test_hydroshare_portal_types_are_stable_in_fingerprint(self):
        first = hydroshare_artifact(portal_types=["Datasets", "Apps"])
        reordered = hydroshare_artifact(portal_types=["apps", "datasets"])
        changed = hydroshare_artifact(
            portal_types=["Apps", "Datasets", "Notebooks"]
        )

        self.assertEqual(
            ["Apps", "Datasets"], get_hydroshare_portal_types(first)
        )
        self.assertEqual(
            _repository_snapshot_fingerprint(first, []),
            _repository_snapshot_fingerprint(reordered, []),
        )
        self.assertNotEqual(
            _repository_snapshot_fingerprint(first, []),
            _repository_snapshot_fingerprint(changed, []),
        )

    def test_hydroshare_snapshot_query_is_scoped_within_type_three(self):
        artifact = hydroshare_artifact()
        db = FakeDatabase(active_rows=[{
            "url": "https://www.hydroshare.org/resource/removed/",
            "metadata": {
                "hydroshare": {
                    "artifact_role": "hydroshare_resource",
                    "resource_id": "removed",
                },
                "sync": {"content_fingerprint": "old"},
            },
        }])

        upserts, deletes, stats = reconcile_artifact_snapshot(
            db, [artifact], [], 3, hydroshare_only=True
        )

        self.assertEqual([artifact["URL"]], [item["URL"] for item in upserts])
        self.assertEqual(
            [{"URL": "https://www.hydroshare.org/resource/removed/"}],
            deletes,
        )
        query, params, _ = db.queries[0]
        self.assertIn("metadata->'hydroshare'", query)
        self.assertIn("ILIKE '%%hydroshare.org/resource/%%'", query)
        self.assertEqual((3,), params)
        self.assertEqual("hydroshare", stats["scope"])

    def test_hydroshare_snapshot_rejects_unmarked_type_three_artifact(self):
        artifact = hydroshare_artifact()
        artifact.pop("artifact_role")

        with self.assertRaisesRegex(RuntimeError, "not marked"):
            reconcile_artifact_snapshot(
                FakeDatabase(), [artifact], [], 3, hydroshare_only=True
            )

    def test_hydroshare_snapshot_rejects_empty_discovery(self):
        with self.assertRaisesRegex(RuntimeError, "snapshot is empty"):
            reconcile_artifact_snapshot(
                FakeDatabase(), [], [], 3, hydroshare_only=True
            )

    def test_hydroshare_snapshot_rejects_large_removal_by_default(self):
        artifacts, active_rows = hydroshare_reconciliation_fixture(
            active_count=20, removal_count=5
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "deactivate 5 of 20.*allow-large-hydroshare-removals",
        ):
            reconcile_artifact_snapshot(
                FakeDatabase(active_rows=active_rows),
                artifacts,
                [],
                3,
                hydroshare_only=True,
            )

    def test_hydroshare_snapshot_allows_large_removal_with_override(self):
        artifacts, active_rows = hydroshare_reconciliation_fixture(
            active_count=20, removal_count=5
        )

        upserts, deletes, stats = reconcile_artifact_snapshot(
            FakeDatabase(active_rows=active_rows),
            artifacts,
            [],
            3,
            hydroshare_only=True,
            allow_large_hydroshare_removals=True,
        )

        self.assertEqual([], upserts)
        self.assertEqual(5, len(deletes))
        self.assertEqual(5, stats["removed_artifacts"])

    def test_hydroshare_large_removal_guard_requires_both_thresholds(self):
        for active_count, removal_count in ((5, 4), (21, 5)):
            with self.subTest(
                active_count=active_count, removal_count=removal_count
            ):
                artifacts, active_rows = hydroshare_reconciliation_fixture(
                    active_count=active_count,
                    removal_count=removal_count,
                )
                _, deletes, _ = reconcile_artifact_snapshot(
                    FakeDatabase(active_rows=active_rows),
                    artifacts,
                    [],
                    3,
                    hydroshare_only=True,
                )
                self.assertEqual(removal_count, len(deletes))

    def test_hydroshare_snapshot_requires_a_portal_type(self):
        artifact = hydroshare_artifact()
        artifact["hs_research_portal_types"] = []

        with self.assertRaisesRegex(RuntimeError, "no research-portal type"):
            reconcile_artifact_snapshot(
                FakeDatabase(), [artifact], [], 3, hydroshare_only=True
            )

    def test_hydroshare_portal_mappings_use_validated_lookup_ids(self):
        artifact = hydroshare_artifact(
            portal_types=["Datasets", "Notebooks", "Datasets"]
        )
        db = FakeDatabase(portal_types=[
            {"idhsresearchportaltype": 2, "hsresearchportaltype": "Datasets"},
            {"idhsresearchportaltype": 6, "hsresearchportaltype": "Notebooks"},
        ])

        inserted = insert_hydroshare_portal_mappings(
            db, [artifact], {artifact["URL"]: 101}
        )

        self.assertEqual(2, inserted)
        self.assertTrue(any(
            "FROM tblhsresearchportaltypes;" in query
            for query, _, _ in db.queries
        ))
        query, rows, _ = db.batches[0]
        self.assertIn("INSERT INTO trlartifactshsresearchportaltypes", query)
        self.assertIn("ON CONFLICT", query)
        self.assertEqual([(101, 2), (101, 6)], rows)

    def test_hydroshare_portal_mapping_rejects_unknown_lookup_name(self):
        artifact = hydroshare_artifact(portal_types=["Unknown"])

        with self.assertRaisesRegex(RuntimeError, "unknown HydroShare"):
            insert_hydroshare_portal_mappings(
                FakeDatabase(), [artifact], {artifact["URL"]: 101}
            )

    def test_unchanged_hydroshare_snapshot_backfills_empty_bridge(self):
        artifact = hydroshare_artifact(portal_types=["Datasets"])
        db = FakeDatabase(
            active_artifact_ids=[{
                "idartifact": 101,
                "url": artifact["URL"],
            }],
            portal_types=[{
                "idhsresearchportaltype": 2,
                "hsresearchportaltype": "Datasets",
            }],
        )

        # There are no artifacts to upsert in this scenario. The complete
        # incoming snapshot is enough to restore a missing bridge row.
        ensured = ensure_hydroshare_snapshot_portal_mappings(db, [artifact])

        self.assertEqual(1, ensured)
        active_query, params, fetch = db.queries[0]
        self.assertIn("idartifacttype = %s", active_query)
        self.assertIn("isactive = TRUE", active_query)
        self.assertEqual(([artifact["URL"]], 3), params)
        self.assertTrue(fetch)
        bridge_query, rows, _ = db.batches[0]
        self.assertIn("ON CONFLICT", bridge_query)
        self.assertEqual([(101, 2)], rows)

    def test_hydroshare_chunk_types_are_seeded_idempotently(self):
        db = FakeDatabase()

        ensure_hydroshare_chunk_types(db)

        query, rows, page_size = db.batches[0]
        self.assertIn("ON CONFLICT", query)
        self.assertEqual(15, len(rows))
        self.assertIn((3, "Readme File"), rows)
        self.assertEqual(15, page_size)

    def test_hydroshare_symbolic_chunk_type_is_resolved_by_name(self):
        db = FakeDatabase(
            chunk_types=[{"idchunktype": 31, "typename": "Abstract"}]
        )
        chunk = repository_chunk(1, 10)
        chunk["chunk_type_name"] = "Abstract"
        artifact = hydroshare_artifact()

        inserted = insert_chunks(
            db,
            [chunk],
            {1: artifact["URL"]},
            {artifact["URL"]: 99},
            3,
        )

        self.assertEqual(1, inserted)
        self.assertEqual(31, db.batches[0][1][0][1])

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

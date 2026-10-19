import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from reuse_local_embeddings import (
    DatabaseArtifact,
    DatabaseChunk,
    DatabaseInventory,
    EmbeddingReuseError,
    SnapshotArtifact,
    SnapshotChunk,
    SnapshotInventory,
    _execute_vector_updates,
    build_snapshot_inventory,
    compare_vector_digests,
    load_database_config,
    main,
    transfer_embeddings,
    validate_database_rows,
    validate_target_vector_conflicts,
)


class FakeConnection:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def small_snapshot(*, empty_text=False):
    artifact = SnapshotArtifact(1, 7, "https://hub.ciroh.org/page", "docuhub")
    chunk = SnapshotChunk(
        artifact_key=artifact.key,
        source_chunk_id=11,
        order=1,
        chunk_type="Section",
        section_hint="Introduction",
        text="" if empty_text else "Chunk body",
        source_name="docuhub",
    )
    return SnapshotInventory(
        artifacts={artifact.key: artifact},
        chunks={chunk.key: chunk},
        source_counts={"docuhub": {"artifacts": 1, "chunks": 1}},
    )


def database_rows(*, empty_text=False, vector="[0,1]"):
    snapshot = small_snapshot(empty_text=empty_text)
    artifact_key = next(iter(snapshot.artifacts))
    chunk_key = next(iter(snapshot.chunks))
    chunk_vector = None if empty_text else vector
    artifacts = {
        artifact_key: DatabaseArtifact(101, vector, 1792),
    }
    chunks = {
        chunk_key: DatabaseChunk(
            201,
            chunk_vector,
            None if chunk_vector is None else 1792,
        )
    }
    return DatabaseInventory(artifacts=artifacts, chunks=chunks)


class SnapshotInventoryTests(unittest.TestCase):
    def test_builds_all_manifest_enabled_sources_with_strict_counts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payloads = {
                "doc_artifacts.json": [{
                    "idArtifact": 1,
                    "idArtifactType": 1,
                    "URL": "https://hub.ciroh.org/page",
                }],
                "doc_chunks.json": [{
                    "idArtifact": 1,
                    "idChunk": 10,
                    "idChunkType": 1,
                    "order": 1,
                    "title": "Intro",
                    "chunk_text": "Page",
                }],
                "github_artifacts.json": [{
                    "idArtifact": 1,
                    "idArtifactType": 4,
                    "URL": "https://github.com/CIROH-UA/repo",
                }],
                "github_chunks.json": [{
                    "idArtifact": 1,
                    "idChunk": 10,
                    "chunk_type_name": "Project Overview",
                    "order": 1,
                    "section_hint": "README",
                    "chunk_text": "Repo",
                }],
                "hs_artifacts.json": [{
                    "idArtifact": 1,
                    "idArtifactType": 3,
                    "URL": "https://www.hydroshare.org/resource/id",
                }],
                "hs_chunks.json": [{
                    "idArtifact": 1,
                    "idChunk": 10,
                    "chunk_type_name": "Abstract",
                    "order": 1,
                    "section_hint": "Abstract",
                    "chunk_text": "Dataset",
                }],
            }
            files = {}
            for role, payload in payloads.items():
                path = root / role
                path.write_text(json.dumps(payload), encoding="utf-8")
                files[role] = path
            validated = {
                "manifest": {
                    "include_github_repositories": True,
                    "include_hydroshare_resources": True,
                },
                "files": {
                    "docuhub_artifacts": files["doc_artifacts.json"],
                    "docuhub_chunks": files["doc_chunks.json"],
                    "github_artifacts": files["github_artifacts.json"],
                    "github_chunks": files["github_chunks.json"],
                    "hydroshare_artifacts": files["hs_artifacts.json"],
                    "hydroshare_chunks": files["hs_chunks.json"],
                },
            }

            inventory = build_snapshot_inventory(
                validated, expected_artifacts=3, expected_chunks=3
            )

            self.assertEqual(3, inventory.artifact_count)
            self.assertEqual(3, inventory.chunk_count)
            self.assertEqual("Intro", inventory.chunks[(1, "https://hub.ciroh.org/page", 10)].section_hint)

    def test_rejects_duplicate_chunk_key(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = root / "artifacts.json"
            chunks = root / "chunks.json"
            artifacts.write_text(json.dumps([{
                "idArtifact": 1,
                "idArtifactType": 1,
                "URL": "https://hub.ciroh.org/page",
            }]), encoding="utf-8")
            repeated = {
                "idArtifact": 1,
                "idChunk": 10,
                "idChunkType": 1,
                "order": 1,
                "chunk_text": "Page",
            }
            chunks.write_text(json.dumps([repeated, repeated]), encoding="utf-8")
            validated = {
                "manifest": {},
                "files": {
                    "docuhub_artifacts": artifacts,
                    "docuhub_chunks": chunks,
                },
            }

            with self.assertRaisesRegex(EmbeddingReuseError, "Duplicate prepared chunk"):
                build_snapshot_inventory(validated)


class DatabaseRowValidationTests(unittest.TestCase):
    def artifact_rows(self, *, vector="[0,1]", dimensions=1792):
        return [{
            "idartifact": 101,
            "idartifacttype": 1,
            "url": "https://hub.ciroh.org/page",
            "embedding_text": vector,
            "embedding_dimensions": dimensions,
        }]

    def chunk_rows(
        self,
        *,
        text="Chunk body",
        vector="[0,1]",
        dimensions=1792,
        order=1,
        chunk_type="Section",
        section_hint="Introduction",
    ):
        return [{
            "idchunk": 201,
            "idartifact": 101,
            "chunk_order": order,
            "chunk_text": text,
            "chunk_type": chunk_type,
            "section_hint": section_hint,
            "source_chunk_id": "11",
            "embedding_text": vector,
            "embedding_dimensions": dimensions,
        }]

    def test_validates_exact_url_source_id_order_type_hint_and_text(self):
        inventory = validate_database_rows(
            small_snapshot(),
            self.artifact_rows(),
            self.chunk_rows(),
            label="Source",
            require_vectors=True,
        )
        self.assertEqual(1, len(inventory.artifacts))
        self.assertEqual(1, len(inventory.chunks))

    def test_rejects_missing_or_wrong_dimension_vector(self):
        with self.assertRaisesRegex(EmbeddingReuseError, "has no embedding"):
            validate_database_rows(
                small_snapshot(),
                self.artifact_rows(),
                self.chunk_rows(vector=None, dimensions=None),
                label="Source",
                require_vectors=True,
            )
        with self.assertRaisesRegex(EmbeddingReuseError, "1792-dimensional"):
            validate_database_rows(
                small_snapshot(),
                self.artifact_rows(dimensions=1536),
                self.chunk_rows(),
                label="Source",
                require_vectors=True,
            )

    def test_empty_chunk_is_the_only_allowed_null_vector(self):
        inventory = validate_database_rows(
            small_snapshot(empty_text=True),
            self.artifact_rows(),
            self.chunk_rows(text="", vector=None, dimensions=None),
            label="Source",
            require_vectors=True,
        )
        self.assertIsNone(next(iter(inventory.chunks.values())).embedding_text)

    def test_rejects_any_structural_chunk_mismatch(self):
        cases = {
            "order": {"order": 2},
            "chunk type": {"chunk_type": "Subsection"},
            "section hint": {"section_hint": "Other"},
            "chunk text": {"text": "Other"},
        }
        for expected_message, changes in cases.items():
            with self.subTest(expected_message=expected_message):
                with self.assertRaisesRegex(EmbeddingReuseError, expected_message):
                    validate_database_rows(
                        small_snapshot(),
                        self.artifact_rows(),
                        self.chunk_rows(**changes),
                        label="Source",
                        require_vectors=True,
                    )


class VectorCopyTests(unittest.TestCase):
    def test_conflicting_existing_target_vector_fails_closed(self):
        source = database_rows(vector="[0,1]")
        target = database_rows(vector="[9,9]")
        with self.assertRaisesRegex(EmbeddingReuseError, "conflicting"):
            validate_target_vector_conflicts(source, target)

    def test_digest_validation_covers_artifacts_and_chunks(self):
        source = database_rows(vector="[0,1]")
        compare_vector_digests(source, database_rows(vector="[0,1]"))
        with self.assertRaisesRegex(EmbeddingReuseError, "digest differs"):
            compare_vector_digests(source, database_rows(vector="[9,9]"))

    @patch("reuse_local_embeddings.execute_values")
    def test_batch_rowcount_mismatch_is_an_error(self, execute_values_mock):
        execute_values_mock.return_value = [(1,)]
        with self.assertRaisesRegex(EmbeddingReuseError, "expected 2"):
            _execute_vector_updates(
                Mock(),
                "UPDATE table SET embedding = v.embedding FROM (VALUES %s) v",
                [(1, "[0]"), (2, "[1]")],
                label="chunk",
            )

    @patch("reuse_local_embeddings._prepare_connection")
    @patch("reuse_local_embeddings._lock_target_tables")
    @patch("reuse_local_embeddings._acquire_target_lock")
    @patch("reuse_local_embeddings.compare_vector_digests")
    @patch("reuse_local_embeddings.apply_embeddings")
    @patch("reuse_local_embeddings.load_database_inventory")
    def test_execute_commits_once_after_post_validation(
        self,
        load_mock,
        apply_mock,
        compare_mock,
        _lock_mock,
        _table_lock_mock,
        _prepare_mock,
    ):
        source_inventory = database_rows()
        target_before = DatabaseInventory(
            artifacts={
                key: DatabaseArtifact(row.database_id, None, None)
                for key, row in source_inventory.artifacts.items()
            },
            chunks={
                key: DatabaseChunk(row.database_id, None, None)
                for key, row in source_inventory.chunks.items()
            },
        )
        load_mock.side_effect = [source_inventory, target_before, source_inventory]
        apply_mock.return_value = {
            "artifact_rows_updated": 1,
            "chunk_rows_updated": 1,
            "artifact_vectors_copied": 1,
            "chunk_vectors_copied": 1,
            "null_empty_chunks_copied": 0,
        }
        source_connection = FakeConnection()
        target_connection = FakeConnection()

        result = transfer_embeddings(
            source_connection,
            target_connection,
            small_snapshot(),
            source_schema="CIROH_AIBot",
            target_schema="CIROH_AIBot",
            execute=True,
        )

        self.assertEqual("execute", result["mode"])
        self.assertEqual(1, target_connection.commits)
        self.assertEqual(0, target_connection.rollbacks)
        self.assertEqual(1, source_connection.rollbacks)
        compare_mock.assert_called_once()

    @patch("reuse_local_embeddings._prepare_connection")
    @patch("reuse_local_embeddings._lock_target_tables")
    @patch("reuse_local_embeddings._acquire_target_lock")
    @patch("reuse_local_embeddings.compare_vector_digests")
    @patch("reuse_local_embeddings.apply_embeddings")
    @patch("reuse_local_embeddings.load_database_inventory")
    def test_post_copy_mismatch_rolls_back_without_commit(
        self,
        load_mock,
        apply_mock,
        compare_mock,
        _lock_mock,
        _table_lock_mock,
        _prepare_mock,
    ):
        inventory = database_rows()
        load_mock.side_effect = [inventory, inventory, inventory]
        apply_mock.return_value = {}
        compare_mock.side_effect = EmbeddingReuseError("digest mismatch")
        source_connection = FakeConnection()
        target_connection = FakeConnection()

        with self.assertRaisesRegex(EmbeddingReuseError, "digest mismatch"):
            transfer_embeddings(
                source_connection,
                target_connection,
                small_snapshot(),
                source_schema="CIROH_AIBot",
                target_schema="CIROH_AIBot",
                execute=True,
            )

        self.assertEqual(0, target_connection.commits)
        self.assertEqual(1, target_connection.rollbacks)

    @patch("reuse_local_embeddings._prepare_connection")
    @patch("reuse_local_embeddings.apply_embeddings")
    @patch("reuse_local_embeddings.load_database_inventory")
    def test_default_dry_run_never_updates_or_commits(
        self,
        load_mock,
        apply_mock,
        _prepare_mock,
    ):
        inventory = database_rows()
        load_mock.side_effect = [inventory, inventory]
        source_connection = FakeConnection()
        target_connection = FakeConnection()

        result = transfer_embeddings(
            source_connection,
            target_connection,
            small_snapshot(),
            source_schema="CIROH_AIBot",
            target_schema="CIROH_AIBot",
            execute=False,
        )

        self.assertEqual("dry_run", result["mode"])
        apply_mock.assert_not_called()
        self.assertEqual(0, target_connection.commits)
        self.assertEqual(1, target_connection.rollbacks)


class ConfigurationAndCliTests(unittest.TestCase):
    def test_dotenv_config_requires_schema_and_hides_password(self):
        with tempfile.TemporaryDirectory() as temporary:
            env_path = Path(temporary) / ".env"
            env_path.write_text(
                "POSTGRES_HOST=localhost\n"
                "POSTGRES_DB=ciroh\n"
                "POSTGRES_SCHEMA=CIROH_AIBot\n"
                "POSTGRES_USER=user\n"
                "POSTGRES_PASSWORD=top-secret\n",
                encoding="utf-8",
            )
            config = load_database_config(env_path)
            self.assertNotIn("top-secret", repr(config))
            env_path.write_text(
                "POSTGRES_HOST=localhost\n"
                "POSTGRES_DB=ciroh\n"
                "POSTGRES_USER=user\n"
                "POSTGRES_PASSWORD=top-secret\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(EmbeddingReuseError, "POSTGRES_SCHEMA"):
                load_database_config(env_path)

    @patch("reuse_local_embeddings.psycopg2.connect")
    @patch("reuse_local_embeddings.validate_prepared_bundle")
    @patch("reuse_local_embeddings.resolve_prepared_bundle")
    def test_bundle_validation_happens_before_any_database_connect(
        self,
        resolve_mock,
        validate_mock,
        connect_mock,
    ):
        with tempfile.TemporaryDirectory() as temporary:
            bundle = Path(temporary) / "bundle"
            bundle.mkdir()
            report = Path(temporary) / "report.json"
            resolve_mock.return_value = bundle
            validate_mock.side_effect = EmbeddingReuseError("invalid bundle")

            with self.assertRaisesRegex(EmbeddingReuseError, "invalid bundle"):
                main([
                    "--bundle",
                    str(bundle),
                    "--target-env",
                    str(Path(temporary) / "target.env"),
                    "--result-file",
                    str(report),
                ])

            connect_mock.assert_not_called()
            self.assertEqual("failed", json.loads(report.read_text())["status"])


if __name__ == "__main__":
    unittest.main()

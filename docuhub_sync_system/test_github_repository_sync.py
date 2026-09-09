import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace

from github_repository_sync import (
    RepositorySyncConfig,
    classify_selection_reason,
    extract_selected_files,
    parse_markdown_sections,
    synchronize_repository_artifacts,
)


def repository_record(description="Hydrology tools"):
    return {
        "id": 1,
        "name": "sample-repo",
        "full_name": "CIROH-UA/sample-repo",
        "html_url": "https://github.com/CIROH-UA/sample-repo",
        "description": description,
        "default_branch": "main",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
        "pushed_at": "2026-01-02T00:00:00Z",
        "language": "Python",
        "topics": ["hydrology"],
        "owner": {"login": "CIROH-UA"},
        "license": None,
    }


def repository_zip():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "CIROH-UA-sample-repo-abc/README.md",
            "# Sample\nTools for hydrologic analysis, modeling, and forecasting.",
        )
        archive.writestr(
            "CIROH-UA-sample-repo-abc/src/internal.py",
            "print('not selected')",
        )
    return buffer.getvalue()


class FakeGitHub:
    def __init__(self, repo=None, sha="abc123"):
        self.repo = repo or repository_record()
        self.sha = sha
        self.download_calls = 0

    def list_org_repositories(self, owner):
        return [self.repo]

    def get_head_sha(self, owner, repository, branch):
        return self.sha

    def get_contributors(self, owner, repository):
        return [{"login": "ciroh-user", "contributions": 3}]

    def download_snapshot(self, owner, repository, sha):
        self.download_calls += 1
        return repository_zip()


class MultiFakeGitHub(FakeGitHub):
    def __init__(self, repositories, sha="abc123"):
        super().__init__(repositories[0], sha=sha)
        self.repositories = repositories

    def list_org_repositories(self, owner):
        return self.repositories


class FakeResponses:
    def __init__(self):
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        is_classifier = "classifier" in kwargs["input"][0]["content"].lower()
        payload = (
            {"chunk_type": "Project Overview", "reason": "Repository introduction"}
            if is_classifier
            else {
                "summary_text": "Sample Repo provides hydrologic analysis tools.",
                "keywords": ["hydrologic analysis"],
                "entities": ["CIROH"],
                "document_type": "scientific software package",
            }
        )
        return SimpleNamespace(
            output_text=json.dumps(payload),
            usage={
                "input_tokens": 100,
                "output_tokens": 20,
                "total_tokens": 120,
            },
        )


class GitHubRepositorySyncTests(unittest.TestCase):
    def test_v2_selection_policy_keeps_docs_and_skips_source_code(self):
        self.assertEqual(
            classify_selection_reason("README.md", "sample-repo"),
            "allowed_exact_filename",
        )
        self.assertEqual(
            classify_selection_reason("examples/tutorial.ipynb", "sample-repo"),
            "allowed_path_prefix",
        )
        self.assertIsNone(
            classify_selection_reason("src/internal.py", "sample-repo")
        )
        self.assertIsNone(
            classify_selection_reason(".github/README.md", "sample-repo")
        )

    def test_archive_path_traversal_is_rejected(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("root/../README.md", "unsafe")
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                extract_selected_files(
                    buffer.getvalue(), Path(temporary), "sample-repo"
                )

    def test_markdown_fenced_heading_is_not_split_into_a_section(self):
        specs = parse_markdown_sections(
            "# Overview\n```markdown\n# not a heading\n```\nRepository body.",
            "README.md",
        )
        self.assertEqual(1, len(specs))
        self.assertEqual("Overview", specs[0]["section_hint"])
        self.assertIn("# not a heading", specs[0]["chunk_text"])

    def test_incremental_run_reuses_artifact_id_and_llm_description(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = RepositorySyncConfig(root=root)
            github = FakeGitHub()
            responses = FakeResponses()
            llm = SimpleNamespace(responses=responses)

            first = synchronize_repository_artifacts(
                config, github, llm_client=llm
            )
            artifacts_path = root / "dashboard/formated_files/coderepo_artifacts.json"
            chunks_path = root / "dashboard/formated_files/coderepo_chunks.json"
            first_artifacts = json.loads(artifacts_path.read_text(encoding="utf-8"))
            first_chunks = json.loads(chunks_path.read_text(encoding="utf-8"))

            self.assertEqual(first["new_count"], 1)
            self.assertEqual(first["summarized_count"], 1)
            self.assertEqual(first["total_chunks"], 1)
            self.assertEqual(first["chunked_repository_count"], 1)
            self.assertEqual(first["openai_usage"]["total_tokens"], 240)
            self.assertEqual(first_artifacts[0]["idArtifact"], 1)
            self.assertIn("hydrologic analysis", first_artifacts[0]["summary_data"]["summary_text"])
            self.assertEqual(first_chunks[0]["idArtifact"], 1)
            self.assertEqual(first_chunks[0]["chunk_type_name"], "Project Overview")
            self.assertIsNone(first_chunks[0]["idChunkType"])
            self.assertEqual(github.download_calls, 1)
            self.assertEqual(responses.calls, 2)

            github_again = FakeGitHub()
            responses_again = FakeResponses()
            second = synchronize_repository_artifacts(
                config,
                github_again,
                llm_client=SimpleNamespace(responses=responses_again),
            )
            second_artifacts = json.loads(artifacts_path.read_text(encoding="utf-8"))
            second_chunks = json.loads(chunks_path.read_text(encoding="utf-8"))

            self.assertEqual(second["unchanged_count"], 1)
            self.assertEqual(second["reused_summary_count"], 1)
            self.assertEqual(second["reused_chunk_repository_count"], 1)
            self.assertEqual(second["openai_usage"]["total_tokens"], 0)
            self.assertEqual(second_artifacts[0]["idArtifact"], 1)
            self.assertEqual(second_chunks, first_chunks)
            self.assertEqual(github_again.download_calls, 0)
            self.assertEqual(responses_again.calls, 0)

    def test_interrupted_run_resumes_completed_repository_checkpoint(self):
        second = repository_record("Second repository")
        second.update(
            {
                "id": 2,
                "name": "second-repo",
                "full_name": "CIROH-UA/second-repo",
                "html_url": "https://github.com/CIROH-UA/second-repo",
            }
        )

        class InterruptOnSecondRepository(FakeResponses):
            def create(self, **kwargs):
                if self.calls == 2:
                    raise KeyboardInterrupt("simulated interruption")
                return super().create(**kwargs)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = RepositorySyncConfig(root=root)
            github = MultiFakeGitHub([repository_record(), second])
            interrupted_responses = InterruptOnSecondRepository()

            with self.assertRaises(KeyboardInterrupt):
                synchronize_repository_artifacts(
                    config,
                    github,
                    llm_client=SimpleNamespace(responses=interrupted_responses),
                )

            checkpoint = root / (
                "local_change_dashboard/github_repository_generation_checkpoint.json"
            )
            checkpoint_payload = json.loads(checkpoint.read_text(encoding="utf-8"))
            self.assertEqual(
                ["CIROH-UA/sample-repo"],
                list(checkpoint_payload["repositories"]),
            )

            resumed_responses = FakeResponses()
            report = synchronize_repository_artifacts(
                config,
                MultiFakeGitHub([repository_record(), second]),
                llm_client=SimpleNamespace(responses=resumed_responses),
            )

            self.assertEqual(1, report["resumed_checkpoint_count"])
            self.assertEqual(2, resumed_responses.calls)
            self.assertEqual(480, report["openai_usage"]["total_tokens"])
            self.assertFalse(checkpoint.exists())

    def test_chunk_generation_can_run_without_any_llm_calls(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = synchronize_repository_artifacts(
                RepositorySyncConfig(root=root),
                FakeGitHub(),
                summarize=False,
            )
            chunks = json.loads(
                (root / "dashboard/formated_files/coderepo_chunks.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(report["openai_usage"]["total_tokens"], 0)
            self.assertEqual(report["deterministic_classification_fallback_count"], 1)
            self.assertEqual(chunks[0]["chunk_type_name"], "Documentation Section")

    def test_metadata_change_resummarizes_without_redownloading_same_sha(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = RepositorySyncConfig(root=root)
            synchronize_repository_artifacts(
                config,
                FakeGitHub(),
                llm_client=SimpleNamespace(responses=FakeResponses()),
            )

            changed_github = FakeGitHub(repository_record("Updated purpose"))
            changed_responses = FakeResponses()
            report = synchronize_repository_artifacts(
                config,
                changed_github,
                llm_client=SimpleNamespace(responses=changed_responses),
            )

            self.assertEqual(report["updated_count"], 1)
            self.assertEqual(report["summarized_count"], 1)
            self.assertEqual(changed_github.download_calls, 0)
            self.assertEqual(changed_responses.calls, 1)

    def test_changed_sha_rebuilds_only_that_repositories_chunks_with_new_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = RepositorySyncConfig(root=root)
            synchronize_repository_artifacts(
                config,
                FakeGitHub(sha="abc123"),
                llm_client=SimpleNamespace(responses=FakeResponses()),
            )
            chunk_path = root / "dashboard/formated_files/coderepo_chunks.json"
            old_chunks = json.loads(chunk_path.read_text(encoding="utf-8"))

            responses = FakeResponses()
            report = synchronize_repository_artifacts(
                config,
                FakeGitHub(sha="def456"),
                llm_client=SimpleNamespace(responses=responses),
            )
            new_chunks = json.loads(chunk_path.read_text(encoding="utf-8"))

            self.assertEqual(report["updated_count"], 1)
            self.assertEqual(report["chunked_repository_count"], 1)
            self.assertGreater(new_chunks[0]["idChunk"], old_chunks[0]["idChunk"])
            self.assertIn("/blob/def456/", new_chunks[0]["type_specific"]["source_url"])
            self.assertEqual(responses.calls, 2)

    def test_deleted_repository_id_is_not_reused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = RepositorySyncConfig(root=root)
            synchronize_repository_artifacts(
                config,
                FakeGitHub(),
                llm_client=SimpleNamespace(responses=FakeResponses()),
            )

            empty_github = FakeGitHub()
            empty_github.list_org_repositories = lambda owner: []
            deleted = synchronize_repository_artifacts(
                config,
                empty_github,
                llm_client=SimpleNamespace(responses=FakeResponses()),
            )
            self.assertEqual(deleted["deleted_count"], 1)

            replacement = repository_record("A different repository")
            replacement.update(
                {
                    "id": 2,
                    "name": "replacement-repo",
                    "full_name": "CIROH-UA/replacement-repo",
                    "html_url": "https://github.com/CIROH-UA/replacement-repo",
                }
            )
            synchronize_repository_artifacts(
                config,
                FakeGitHub(replacement),
                llm_client=SimpleNamespace(responses=FakeResponses()),
            )
            artifacts = json.loads(
                (root / "dashboard/formated_files/coderepo_artifacts.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(artifacts[0]["idArtifact"], 2)


if __name__ == "__main__":
    unittest.main()

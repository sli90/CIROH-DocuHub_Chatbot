import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from hydroshare_sync import (
    MAX_ARTIFACT_SUMMARY_CHARS,
    MAX_README_CHUNK_CHARS,
    PORTAL_CATEGORY_SUBJECTS,
    build_hydroshare_artifact,
    build_hydroshare_chunks,
    discover_hydroshare_resources,
    synchronize_hydroshare_resources,
)


RESOURCE_A = "a" * 32
RESOURCE_B = "b" * 32
RESOURCE_C = "c" * 32


class FakeResponse:
    def __init__(self, *, text="", payload=None):
        self.text = text
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, community_ids=None):
        self.community_ids = list(community_ids or [])
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params, timeout))
        if "/community/" in url:
            return FakeResponse(
                text='<script id="community-app-data" type="application/json">'
                '{"members":[{"id":19,"name":"CIROH"}]}</script>'
            )
        return FakeResponse(
            payload={
                "results": [
                    {
                        "resource_id": resource_id.upper(),
                        "resource_title": "Community dataset",
                    }
                    for resource_id in self.community_ids
                ],
                "next": None,
            }
        )


def resource_payload(resource_id, *, checksum="sum-1", updated="2026-04-01"):
    metadata = {
        "title": f"Resource {resource_id[0].upper()}",
        "url": f"https://www.hydroshare.org/resource/{resource_id}",
        "type": "CompositeResource",
        "abstract": "A useful hydrologic dataset.",
        "subjects": ["hydrology", "CIROH"],
        "spatial_coverage": {
            "type": "box",
            "northlimit": 42,
            "southlimit": 40,
            "eastlimit": -110,
            "westlimit": -112,
        },
        "period_coverage": {"start": "2020-01-01", "end": "2020-12-31"},
        "citation": "Example citation",
        "rights": {"statement": "CC BY", "url": "https://example.test/license"},
        "creators": [{"name": "Ada", "organization": "CIROH"}],
        "contributors": [{"name": "Grace"}],
        "awards": [{"funding_agency_name": "NOAA", "number": "A1"}],
        "additional_metadata": {"Model": "NWM"},
        "variables": [
            {
                "name": "streamflow",
                "unit": "m3/s",
                "description": "Simulated discharge",
            }
        ],
        "relations": [
            {
                "type": "The content of this resource references",
                "value": "https://example.test/source",
            }
        ],
    }
    system = {
        "resource_url": metadata["url"],
        "date_created": "2026-03-01",
        "date_last_updated": updated,
        "doi": "10.1234/example",
        "public": True,
        "discoverable": True,
        "content_types": ["GenericLogicalFile"],
    }
    file_object = SimpleNamespace(
        name="README.md",
        path="data/README.md",
        extension=".md",
        checksum=checksum,
        url=f"readme://{resource_id}",
    )
    return SimpleNamespace(
        metadata=metadata,
        metadata_path=f"metadata://{resource_id}",
        system_metadata=lambda: system,
        files=lambda: [file_object],
    )


class FakeHydroShare:
    def __init__(self, resources=None, searches=None):
        self.resources = resources or {
            RESOURCE_A: resource_payload(RESOURCE_A),
            RESOURCE_B: resource_payload(RESOURCE_B),
            RESOURCE_C: resource_payload(RESOURCE_C),
        }
        self.searches = searches or {}
        self.resource_calls = []
        self.retrievals = {}
        for resource_id in self.resources:
            self.retrievals[f"metadata://{resource_id}"] = (
                '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
                'xmlns:hsterms="https://www.hydroshare.org/terms/">'
                "<hsterms:CompositeResource /></rdf:RDF>"
            )
            self.retrievals[f"readme://{resource_id}"] = (
                "# Overview\nHydrologic resource documentation.\n"
                "## Usage\nOpen the resource URL."
            )

    def search(self, subject):
        return [SimpleNamespace(resource_id=value) for value in self.searches.get(subject[0], [])]

    def resource(self, resource_id):
        self.resource_calls.append(resource_id)
        return self.resources[resource_id]

    def retrieve_string(self, url):
        return self.retrievals[url]


def complete_searches():
    return {
        "nwm_portal_app": [RESOURCE_A.upper(), RESOURCE_A],
        "ciroh_hub_notebook": [RESOURCE_A],
        "ciroh_hub_data": [RESOURCE_C],
    }


class HydroShareSyncTests(unittest.TestCase):
    def test_category_constants_match_portal_notebook(self):
        self.assertEqual(
            {
                "Apps": ("nwm_portal_app", "ciroh_hub_app"),
                "Datasets": ("ciroh_portal_data", "ciroh_hub_data"),
                "Courses": ("nwm_portal_module", "ciroh_hub_module"),
                "Presentations": (
                    "ciroh_portal_presentation",
                    "ciroh_hub_presentation",
                ),
                "Events": ("ciroh_hub_event",),
                "Notebooks": ("ciroh_hub_notebook",),
            },
            PORTAL_CATEGORY_SUBJECTS,
        )

    def test_discovery_deduplicates_ids_and_preserves_multiple_memberships(self):
        result = discover_hydroshare_resources(
            FakeHydroShare(searches=complete_searches()),
            session=FakeSession([RESOURCE_B, RESOURCE_C]),
        )
        self.assertEqual([RESOURCE_A, RESOURCE_B, RESOURCE_C], list(result))
        self.assertEqual(["Apps", "Notebooks"], result[RESOURCE_A]["portal_types"])
        self.assertEqual(["Datasets"], result[RESOURCE_B]["portal_types"])
        self.assertEqual(["Datasets"], result[RESOURCE_C]["portal_types"])

    def test_generation_builds_expected_artifact_and_useful_chunks(self):
        with tempfile.TemporaryDirectory() as temporary:
            client = FakeHydroShare(searches=complete_searches())
            report = synchronize_hydroshare_resources(
                temporary,
                client=client,
                session=FakeSession([RESOURCE_B]),
            )
            root = Path(temporary)
            artifacts = json.loads(
                (root / "dashboard/formated_files/hydroshare_artifacts.json").read_text(
                    encoding="utf-8"
                )
            )
            chunks = json.loads(
                (root / "dashboard/formated_files/hydroshare_chunks.json").read_text(
                    encoding="utf-8"
                )
            )
            artifact_a = next(item for item in artifacts if item["resource_id"] == RESOURCE_A)
            self.assertEqual(3, artifact_a["idArtifactType"])
            self.assertEqual("hydroshare_resource", artifact_a["artifact_role"])
            self.assertEqual(["Apps", "Notebooks"], artifact_a["hs_research_portal_types"])
            self.assertEqual("2026-04-01", artifact_a["date_last_updated"])
            self.assertEqual(
                f"https://www.hydroshare.org/resource/{RESOURCE_A}/",
                artifact_a["URL"],
            )
            self.assertEqual(
                "Resource A. A useful hydrologic dataset.",
                artifact_a["summary_data"]["summary_text"],
            )
            self.assertEqual(
                ["hydrology", "CIROH"], artifact_a["summary_data"]["keywords"]
            )
            self.assertEqual(
                "deterministic_hydroshare_metadata",
                artifact_a["summary_data"]["generation_method"],
            )
            self.assertFalse(report["database_update_performed"])
            self.assertEqual(3, report["new_count"])
            self.assertEqual(4, report["portal_membership_count"])
            chunk_types = {item["chunk_type_name"] for item in chunks}
            self.assertTrue(
                {
                    "Abstract",
                    "Spatial Coverage",
                    "Temporal Coverage",
                    "Variable Metadata",
                    "Data Services Info",
                    "File Description",
                    "Subject Keywords",
                    "Citation",
                    "Creator",
                    "Contributor",
                    "Funding Agency",
                    "Additional Metadata",
                    "Related Resources Context",
                    "Readme File",
                }.issubset(chunk_types)
            )
            self.assertTrue(all(item["idChunkType"] is None for item in chunks))

    def test_unchanged_resources_reuse_exact_artifacts_and_chunks(self):
        with tempfile.TemporaryDirectory() as temporary:
            client = FakeHydroShare(searches={"nwm_portal_app": [RESOURCE_A]})
            session = FakeSession([])
            first = synchronize_hydroshare_resources(
                temporary, client=client, session=session
            )
            root = Path(temporary)
            artifact_path = root / "dashboard/formated_files/hydroshare_artifacts.json"
            chunk_path = root / "dashboard/formated_files/hydroshare_chunks.json"
            first_artifacts = artifact_path.read_text(encoding="utf-8")
            first_chunks = chunk_path.read_text(encoding="utf-8")

            second = synchronize_hydroshare_resources(
                temporary,
                client=FakeHydroShare(searches={"nwm_portal_app": [RESOURCE_A]}),
                session=FakeSession([]),
            )
            self.assertEqual(1, first["new_count"])
            self.assertEqual(1, second["unchanged_count"])
            self.assertEqual(1, second["reused_count"])
            self.assertEqual(first_artifacts, artifact_path.read_text(encoding="utf-8"))
            self.assertEqual(first_chunks, chunk_path.read_text(encoding="utf-8"))

    def test_artifact_summary_is_bounded_without_truncating_abstract_metadata(self):
        abstract = "long abstract " * 2_000
        snapshot = {
            "metadata": {
                "title": "Long resource",
                "abstract": abstract,
                "subjects": ["hydrology"],
            },
            "system_metadata": {},
        }
        artifact = build_hydroshare_artifact(
            RESOURCE_A, 1, snapshot, ["Datasets"]
        )
        self.assertEqual(abstract.strip(), artifact["abstract"])
        self.assertLessEqual(
            len(artifact["summary_data"]["summary_text"]),
            MAX_ARTIFACT_SUMMARY_CHARS,
        )
        self.assertTrue(artifact["summary_data"]["summary_text"].endswith("…"))

    def test_checksum_change_rebuilds_with_new_chunk_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            searches = {"ciroh_hub_data": [RESOURCE_A]}
            synchronize_hydroshare_resources(
                temporary,
                client=FakeHydroShare(searches=searches),
                session=FakeSession([]),
            )
            path = Path(temporary) / "dashboard/formated_files/hydroshare_chunks.json"
            old_chunks = json.loads(path.read_text(encoding="utf-8"))
            changed = FakeHydroShare(
                resources={RESOURCE_A: resource_payload(RESOURCE_A, checksum="sum-2")},
                searches=searches,
            )
            report = synchronize_hydroshare_resources(
                temporary, client=changed, session=FakeSession([])
            )
            new_chunks = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(1, report["updated_count"])
            self.assertGreater(new_chunks[0]["idChunk"], old_chunks[-1]["idChunk"])

    def test_removed_resource_is_omitted_and_its_id_is_not_reused(self):
        with tempfile.TemporaryDirectory() as temporary:
            synchronize_hydroshare_resources(
                temporary,
                client=FakeHydroShare(searches={"nwm_portal_app": [RESOURCE_A]}),
                session=FakeSession([]),
            )
            replacement = synchronize_hydroshare_resources(
                temporary,
                client=FakeHydroShare(searches={"nwm_portal_app": [RESOURCE_B]}),
                session=FakeSession([]),
            )
            artifacts = json.loads(
                (
                    Path(temporary)
                    / "dashboard/formated_files/hydroshare_artifacts.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual([RESOURCE_A], replacement["removed_resource_ids"])
            self.assertEqual(1, replacement["new_count"])
            self.assertEqual(2, artifacts[0]["idArtifact"])

    def test_empty_discovery_preserves_previous_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            synchronize_hydroshare_resources(
                temporary,
                client=FakeHydroShare(searches={"nwm_portal_app": [RESOURCE_A]}),
                session=FakeSession([]),
            )
            root = Path(temporary)
            artifact_path = root / "dashboard/formated_files/hydroshare_artifacts.json"
            state_path = root / "local_change_dashboard/hydroshare_sync.json"
            artifacts_before = artifact_path.read_text(encoding="utf-8")
            state_before = state_path.read_text(encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "no resources"):
                synchronize_hydroshare_resources(
                    temporary,
                    client=FakeHydroShare(searches={}),
                    session=FakeSession([]),
                )

            self.assertEqual(artifacts_before, artifact_path.read_text(encoding="utf-8"))
            self.assertEqual(state_before, state_path.read_text(encoding="utf-8"))

            with self.assertRaisesRegex(RuntimeError, "cannot be overridden"):
                synchronize_hydroshare_resources(
                    temporary,
                    client=FakeHydroShare(searches={}),
                    session=FakeSession([]),
                    allow_large_removals=True,
                )

    def test_partial_nonempty_discovery_requires_explicit_large_removal_override(self):
        with tempfile.TemporaryDirectory() as temporary:
            resource_ids = [f"{number:032x}" for number in range(1, 13)]
            resources = {
                resource_id: resource_payload(resource_id)
                for resource_id in resource_ids
            }
            synchronize_hydroshare_resources(
                temporary,
                client=FakeHydroShare(
                    resources=resources,
                    searches={"nwm_portal_app": resource_ids},
                ),
                session=FakeSession([]),
            )
            root = Path(temporary)
            artifact_path = root / "dashboard/formated_files/hydroshare_artifacts.json"
            chunk_path = root / "dashboard/formated_files/hydroshare_chunks.json"
            state_path = root / "local_change_dashboard/hydroshare_sync.json"
            before = (
                artifact_path.read_text(encoding="utf-8"),
                chunk_path.read_text(encoding="utf-8"),
                state_path.read_text(encoding="utf-8"),
            )
            partial_ids = resource_ids[:6]
            partial_client = FakeHydroShare(
                resources=resources,
                searches={"nwm_portal_app": partial_ids},
            )

            with self.assertRaisesRegex(RuntimeError, "would remove 6 of 12"):
                synchronize_hydroshare_resources(
                    temporary,
                    client=partial_client,
                    session=FakeSession([]),
                )

            self.assertEqual(before[0], artifact_path.read_text(encoding="utf-8"))
            self.assertEqual(before[1], chunk_path.read_text(encoding="utf-8"))
            self.assertEqual(before[2], state_path.read_text(encoding="utf-8"))
            failed_report = json.loads(
                (
                    root / "dashboard/formated_files/hydroshare_generation_report.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("failed", failed_report["status"])
            self.assertTrue(failed_report["discovery_shrink_guard"]["triggered"])

            accepted = synchronize_hydroshare_resources(
                temporary,
                client=FakeHydroShare(
                    resources=resources,
                    searches={"nwm_portal_app": partial_ids},
                ),
                session=FakeSession([]),
                allow_large_removals=True,
            )
            self.assertEqual(6, accepted["removed_count"])
            self.assertFalse(accepted["discovery_shrink_guard"]["triggered"])
            self.assertTrue(
                accepted["discovery_shrink_guard"]["allow_large_removals"]
            )

    def test_readme_sections_are_bounded_and_keep_hierarchy_across_files(self):
        parent_body = " ".join(f"token-{index:05d}" for index in range(3000))
        snapshot = {
            "metadata": {},
            "system_metadata": {},
            "file_inventory": [],
            "raw_metadata_xml": "",
            "readmes": [
                {
                    "file_name": "README.md",
                    "text": (
                        f"# Parent\n{parent_body}\n"
                        "## Child\nChild content from the first README."
                    ),
                },
                {
                    "file_name": "README.txt",
                    "text": (
                        "# Second parent\nSecond parent content.\n"
                        "## Second child\nSecond child content."
                    ),
                },
            ],
        }
        chunks, next_chunk_id = build_hydroshare_chunks(
            artifact_id=9,
            next_chunk_id=100,
            resource_id=RESOURCE_A,
            snapshot=snapshot,
        )
        readme_chunks = [
            chunk for chunk in chunks if chunk["chunk_type_name"] == "Readme File"
        ]
        self.assertEqual(100 + len(readme_chunks), next_chunk_id)
        self.assertTrue(
            all(len(chunk["chunk_text"]) <= MAX_README_CHUNK_CHARS for chunk in readme_chunks)
        )
        self.assertEqual(
            len(readme_chunks), len({chunk["idChunk"] for chunk in readme_chunks})
        )

        first_parent_parts = [
            chunk for chunk in readme_chunks if chunk["section_hint"] == "Parent"
        ]
        self.assertGreater(len(first_parent_parts), 1)
        first_parent_id = first_parent_parts[0]["idChunk"]
        self.assertIsNone(first_parent_parts[0]["idChunkParent"])
        self.assertTrue(
            all(
                chunk["idChunkParent"] == first_parent_id
                for chunk in first_parent_parts[1:]
            )
        )
        first_child = next(
            chunk for chunk in readme_chunks if chunk["section_hint"] == "Child"
        )
        self.assertEqual(first_parent_id, first_child["idChunkParent"])

        second_parent = next(
            chunk
            for chunk in readme_chunks
            if chunk["section_hint"] == "Second parent"
        )
        second_child = next(
            chunk
            for chunk in readme_chunks
            if chunk["section_hint"] == "Second child"
        )
        self.assertIsNone(second_parent["idChunkParent"])
        self.assertEqual(second_parent["idChunk"], second_child["idChunkParent"])
        self.assertNotEqual(first_parent_id, second_parent["idChunk"])

    def test_inaccessible_resource_is_skipped_on_first_baseline(self):
        with tempfile.TemporaryDirectory() as temporary:
            client = FakeHydroShare(
                searches={"nwm_portal_app": [RESOURCE_A]}
            )
            client.resource = lambda resource_id: (_ for _ in ()).throw(
                RuntimeError("HTTP 401 Client Error: Unauthorized")
            )

            report = synchronize_hydroshare_resources(
                temporary, client=client, session=FakeSession([])
            )
            root = Path(temporary)
            artifacts = json.loads(
                (
                    root / "dashboard/formated_files/hydroshare_artifacts.json"
                ).read_text(encoding="utf-8")
            )
            chunks = json.loads(
                (
                    root / "dashboard/formated_files/hydroshare_chunks.json"
                ).read_text(encoding="utf-8")
            )
            state = json.loads(
                (root / "local_change_dashboard/hydroshare_sync.json").read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual("completed", report["status"])
            self.assertEqual([], report["errors"])
            self.assertEqual(1, report["inaccessible_count"])
            self.assertEqual([RESOURCE_A], report["inaccessible_resource_ids"])
            self.assertEqual(1, report["inaccessible_skipped_count"])
            self.assertEqual(0, report["inaccessible_preserved_count"])
            self.assertEqual(
                "skipped_new_resource",
                report["inaccessible_errors"][0]["action"],
            )
            self.assertIn("401", report["inaccessible_errors"][0]["error"])
            self.assertEqual([], artifacts)
            self.assertEqual([], chunks)
            self.assertEqual({}, state["resources"])

    def test_temporarily_inaccessible_resource_preserves_previous_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            searches = {"nwm_portal_app": [RESOURCE_A, RESOURCE_B]}
            synchronize_hydroshare_resources(
                temporary,
                client=FakeHydroShare(searches=searches),
                session=FakeSession([]),
            )
            root = Path(temporary)
            artifact_path = root / "dashboard/formated_files/hydroshare_artifacts.json"
            chunk_path = root / "dashboard/formated_files/hydroshare_chunks.json"
            state_path = root / "local_change_dashboard/hydroshare_sync.json"
            artifacts_before = json.loads(artifact_path.read_text(encoding="utf-8"))
            chunks_before = json.loads(chunk_path.read_text(encoding="utf-8"))
            state_before = json.loads(state_path.read_text(encoding="utf-8"))

            client = FakeHydroShare(searches=searches)
            original_resource = client.resource

            def resource_with_forbidden(resource_id):
                if resource_id == RESOURCE_B:
                    raise RuntimeError("403 Client Error: Forbidden")
                return original_resource(resource_id)

            client.resource = resource_with_forbidden
            report = synchronize_hydroshare_resources(
                temporary, client=client, session=FakeSession([])
            )

            artifacts_after = json.loads(artifact_path.read_text(encoding="utf-8"))
            chunks_after = json.loads(chunk_path.read_text(encoding="utf-8"))
            state_after = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual("completed", report["status"])
            self.assertEqual([], report["errors"])
            self.assertEqual(1, report["inaccessible_count"])
            self.assertEqual([RESOURCE_B], report["inaccessible_resource_ids"])
            self.assertEqual(1, report["inaccessible_preserved_count"])
            self.assertEqual(0, report["inaccessible_skipped_count"])
            self.assertEqual(
                "preserved_previous_snapshot",
                report["inaccessible_errors"][0]["action"],
            )
            self.assertEqual([], report["removed_resource_ids"])
            self.assertEqual(2, report["reused_count"])
            self.assertEqual(artifacts_before, artifacts_after)
            self.assertEqual(chunks_before, chunks_after)
            self.assertEqual(
                state_before["resources"][RESOURCE_B],
                state_after["resources"][RESOURCE_B],
            )

    def test_resource_failure_preserves_previous_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            searches = {"nwm_portal_app": [RESOURCE_A]}
            synchronize_hydroshare_resources(
                temporary,
                client=FakeHydroShare(searches=searches),
                session=FakeSession([]),
            )
            root = Path(temporary)
            artifact_path = root / "dashboard/formated_files/hydroshare_artifacts.json"
            before = artifact_path.read_text(encoding="utf-8")
            broken = FakeHydroShare(searches=searches)
            broken.resource = lambda resource_id: (_ for _ in ()).throw(RuntimeError("offline"))
            with self.assertRaises(RuntimeError):
                synchronize_hydroshare_resources(
                    temporary, client=broken, session=FakeSession([])
                )
            self.assertEqual(before, artifact_path.read_text(encoding="utf-8"))
            report = json.loads(
                (
                    root / "dashboard/formated_files/hydroshare_generation_report.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("failed", report["status"])
            self.assertEqual(0, report["inaccessible_count"])


if __name__ == "__main__":
    unittest.main()

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_REPO_AVAILABLE = (ROOT / "ciroh_hub").is_dir()
requires_upstream_repo = unittest.skipUnless(
    UPSTREAM_REPO_AVAILABLE,
    "requires the ciroh_hub checkout created by the first synchronization",
)


def load_backend():
    path = ROOT / "dashboard" / "backend" / "app.py"
    spec = importlib.util.spec_from_file_location("ciroh_backend_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.REPO_ROOT = str(ROOT / "ciroh_hub")
    module.LOCAL_CONTENT_MANIFEST_PATH = str(
        ROOT / "local_change_dashboard" / "local_content_manifest.json"
    )
    return module


class LocalContentPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = load_backend()
        cls.manifest = cls.backend._load_local_content_manifest()

    @requires_upstream_repo
    def test_manifest_sources_exist(self):
        missing = []
        for rule in self.manifest["pages"]:
            for source in rule.get("sources", []):
                path = ROOT / "ciroh_hub" / source["path"]
                if not path.is_file():
                    missing.append(source["path"])
        authors = ROOT / "ciroh_hub" / self.manifest["blog_authors"]["source"]
        if not authors.is_file():
            missing.append(str(authors))
        self.assertEqual([], missing)

    def test_publications_are_excluded(self):
        self.assertTrue(
            self.backend._is_excluded_content_path("docs/publications/intro.mdx")
        )
        self.assertTrue(
            self.backend._is_excluded_content_path("src/pages/publications/index.js")
        )
        self.assertFalse(self.backend._is_excluded_content_path("docs/products/intro.mdx"))

    def test_src_pages_frontmatter_paths_are_domain_root_relative(self):
        cases = {
            "src/pages/impact.mdx": "impact",
            "src/pages/contact.mdx": "contact",
            "src/pages/resources/guide.md": "resources/guide",
            "docs/products/intro.mdx": "docs/products/intro",
        }
        for source_path, expected in cases.items():
            self.assertEqual(
                expected,
                self.backend._frontmatter_path_for_output_rel(source_path),
            )

    @requires_upstream_repo
    def test_working_groups_are_structured(self):
        source = (
            ROOT / "ciroh_hub" / "src" / "data" / "workingGroupsData.js"
        ).read_text(encoding="utf-8")
        parsed = self.backend._parse_static_js_literal(source)
        self.assertIsInstance(parsed, list)
        self.assertGreaterEqual(len(parsed), 8)
        self.assertEqual("Flood Inundation Mapping Working Group", parsed[0]["title"])

    @requires_upstream_repo
    def test_empty_feature_override_does_not_emit_example_comments(self):
        page = ROOT / "ciroh_hub" / "src" / "pages" / "apps" / "index.js"
        content = page.read_text(encoding="utf-8")
        sections, _hash = self.backend._extract_imported_data_text(
            content, "src/pages/apps/index.js"
        )
        self.assertEqual([], sections)

    @requires_upstream_repo
    def test_required_targets_render_local_content(self):
        targets = {
            "src/pages/contribute/index.js": "Contribute HydroShare resources",
            "src/pages/contribute/develop.js": "Develop applications with Tethys",
            "src/pages/impact.mdx": "Community impact data",
            "src/pages/working-groups/index.js": "Flood Inundation Mapping Working Group",
            "src/pages/news.mdx": "June 2026 Update",
            "docs/products/intro.mdx": "NextGen In A Box",
            "src/pages/index.js": "Explore CIROH resources",
        }
        for target, expected in targets.items():
            content = (ROOT / "ciroh_hub" / target).read_text(encoding="utf-8")
            _rule, sections, dependencies = self.backend._local_content_for_target(
                target, content
            )
            rendered = "\n".join(sections)
            self.assertIn(expected, rendered, target)
            self.assertFalse(any(dep.get("missing") for dep in dependencies), target)

    @requires_upstream_repo
    def test_blog_author_ids_resolve_into_content(self):
        blog = ROOT / "ciroh_hub" / "blog" / "2025-02-28-PSU.mdx"
        content = blog.read_text(encoding="utf-8")
        rule, sections, dependencies = self.backend._local_content_for_target(
            "blog/2025-02-28-PSU.mdx", content
        )
        rendered = "\n".join(sections)
        self.assertEqual({}, rule)
        self.assertIn("Arpita Patel", rendered)
        self.assertIn("Yalan Song", rendered)
        self.assertIn("Tadd Bindas", rendered)
        self.assertEqual("blog/authors.yaml", dependencies[0]["path"])


if __name__ == "__main__":
    unittest.main()

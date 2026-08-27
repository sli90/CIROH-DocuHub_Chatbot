import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_generator():
    path = ROOT / "dashboard" / "generate_formatted_files.py"
    spec = importlib.util.spec_from_file_location("ciroh_generator_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RouteConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_generator()

    def test_src_pages_frontmatter_path_maps_to_domain_root(self):
        url = self.generator.build_url(
            {"path": "src/pages/impact"}, "src/pages/impact.mdx"
        )
        self.assertEqual("https://hub.ciroh.org/impact/", url)

    def test_regular_doc_path_is_unchanged(self):
        url = self.generator.build_url(
            {"path": "docs/products/intro"}, "docs/products/intro.mdx"
        )
        self.assertEqual("https://hub.ciroh.org/docs/products/intro/", url)


if __name__ == "__main__":
    unittest.main()

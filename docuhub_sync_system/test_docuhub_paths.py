import unittest

from docuhub_paths import (
    normalize_public_route_path,
    public_route_from_mixed_doc_path,
)


class DocuHubPathTests(unittest.TestCase):
    def test_src_pages_file_maps_to_domain_root(self):
        self.assertEqual(
            "impact", public_route_from_mixed_doc_path("src/pages/impact.mdx")
        )

    def test_nested_src_pages_file_keeps_route_subdirectories(self):
        self.assertEqual(
            "resources/guide",
            public_route_from_mixed_doc_path("src\\pages\\resources\\guide.md"),
        )

    def test_regular_docs_path_is_unchanged(self):
        self.assertEqual(
            "docs/products/intro",
            public_route_from_mixed_doc_path("docs/products/intro.mdx"),
        )

    def test_existing_frontmatter_path_is_normalized(self):
        self.assertEqual(
            "contact", normalize_public_route_path("/src/pages/contact/")
        )


if __name__ == "__main__":
    unittest.main()

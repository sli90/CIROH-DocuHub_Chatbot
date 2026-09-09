import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from local_change_dashboard import external_repo_checker


class ExternalRepositoryCheckerTests(unittest.TestCase):
    def test_moved_ngen_contribution_file_uses_current_upstream_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(
                external_repo_checker,
                "_get_raw",
                return_value=b"current contribution instructions",
            ) as get_raw:
                target, relative = external_repo_checker._download_readme(
                    "CIROH-UA/ngen-datastream",
                    "docs/nrds/CONTRIBUTE.md",
                    "main",
                    temporary,
                )

            requested_url = get_raw.call_args.args[0]
            self.assertIn("docs/nrds/contribute/CONTRIBUTING.md", requested_url)
            self.assertEqual(
                "CIROH-UA/ngen-datastream/docs/nrds/CONTRIBUTE.md",
                relative,
            )
            self.assertEqual(
                "current contribution instructions",
                Path(target).read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()

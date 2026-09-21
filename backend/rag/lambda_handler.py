"""Lambda entry point: wraps the existing FastAPI app with Mangum, unchanged
in shape (AWS Migration Plan, Section 3.2 and Appendix A).

Deployed with this file's directory (`backend/rag/`) as part of the Lambda
package, alongside `main.py`, `ask.py` and `database/`, `aws/` as siblings
under `backend/` (see infra/stacks/backend_stack.py). The explicit
sys.path insert makes `from main import app` resolve the same way whether
Lambda imports this module as `rag.lambda_handler` or `lambda_handler`,
matching the sys.path pattern ask.py already relies on for local runs.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from main import app  # noqa: E402
from mangum import Mangum  # noqa: E402

handler = Mangum(app)

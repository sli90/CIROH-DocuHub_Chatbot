"""Canonical mapping from repository paths to public DocuHub routes."""
from __future__ import annotations

import os


SRC_PAGES_PREFIX = "src/pages/"


def normalize_public_route_path(path: str) -> str:
    """Map a route-like path to its public domain-root-relative value."""
    route = str(path or "").replace("\\", "/").strip("/")
    if route.startswith(SRC_PAGES_PREFIX):
        route = route[len(SRC_PAGES_PREFIX) :]
    return route


def public_route_from_mixed_doc_path(relative_path: str) -> str:
    """Remove the markdown extension, then apply DocuHub route semantics."""
    normalized = str(relative_path or "").replace("\\", "/").lstrip("/")
    without_extension = os.path.splitext(normalized)[0]
    return normalize_public_route_path(without_extension)

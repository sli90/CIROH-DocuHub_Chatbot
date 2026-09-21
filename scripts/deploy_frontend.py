"""Build the frontend for production and redeploy the CDK stack to publish it.

Wraps docs/AWS_DEPLOYMENT.md step 4 (`VITE_API_BASE_URL="" npm run build`,
then `cdk deploy`) as one command, cross-platform (Windows/macOS/Linux) -
no shell-specific env-var syntax to get wrong between PowerShell and bash.

Usage:
    python scripts/deploy_frontend.py
    python scripts/deploy_frontend.py --context allowed_origins=https://chat.ciroh.org
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = REPO_ROOT / "frontend"
INFRA_DIR = REPO_ROOT / "infra"


def run(cmd: list[str], cwd: Path, env: dict | None = None) -> None:
    print(f"$ {' '.join(cmd)}  (in {cwd})")
    result = subprocess.run(cmd, cwd=cwd, env=env, shell=(sys.platform == "win32"))
    if result.returncode != 0:
        sys.exit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--context",
        action="append",
        default=[],
        metavar="key=value",
        help="Extra CDK context value, repeatable (e.g. --context allowed_origins=https://...).",
    )
    parser.add_argument("--skip-install", action="store_true", help="Skip `npm install`.")
    args = parser.parse_args()

    import os

    env = os.environ.copy()
    # Same-origin in production: the frontend is served from the same
    # CloudFront distribution as the API (see AWS_ARCHITECTURE.md).
    env["VITE_API_BASE_URL"] = ""

    if not args.skip_install:
        run(["npm", "install"], cwd=FRONTEND_DIR, env=env)
    run(["npm", "run", "build"], cwd=FRONTEND_DIR, env=env)

    cdk_cmd = ["cdk", "deploy", "CirohStack", "--require-approval", "never"]
    for ctx in args.context:
        cdk_cmd += ["-c", ctx]
    run(cdk_cmd, cwd=INFRA_DIR, env=env)

    print("\nDone. Frontend built and CDK stack redeployed (BucketDeployment invalidates CloudFront automatically).")


if __name__ == "__main__":
    main()

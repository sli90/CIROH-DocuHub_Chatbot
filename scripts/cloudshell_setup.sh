# Prepare an AWS CloudShell session to deploy this project.
#
# Run it with `source` (not bash) at the start of EVERY CloudShell session,
# from the unzipped project folder:
#
#     cd ~/ciroh && source scripts/cloudshell_setup.sh
#
# Safe to re-run: CloudShell wipes everything outside your home directory
# when a session ends, so this re-installs Python 3.12 if needed, reuses
# the virtualenv kept in your home directory, and activates it in your
# current shell. See docs/AWS_DEPLOYMENT_CLOUDSHELL.md.
#
# Deliberately no `set -e`: this file is sourced, and `set -e` would close
# your CloudShell terminal on the first error.

_ciroh_setup() {
    local repo_root venv py
    repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    venv="$HOME/.ciroh-venv"

    # Everything in this project lives in us-east-1, whichever region the
    # console happened to open CloudShell in.
    export AWS_REGION=us-east-1
    export AWS_DEFAULT_REGION=us-east-1

    # CloudShell's home directory is capped at 1 GB: no pip download cache,
    # and drop CDK's build output (regenerated on every deploy; old Lambda
    # bundles would otherwise pile up at ~50 MB each).
    export PIP_NO_CACHE_DIR=1
    rm -rf "$repo_root/infra/cdk.out"

    # Prefer CloudShell's own python3 (3.13 at the time of writing): it is
    # part of the base image, so the venv built on it survives sessions.
    py=""
    for candidate in python3 python3.12 python3.11; do
        if command -v "$candidate" >/dev/null 2>&1 \
            && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
            py="$candidate"; break
        fi
    done
    if [ -z "$py" ]; then
        echo "Installing Python 3.12 (needed once per CloudShell session, ~30s)..."
        if sudo dnf install -y -q python3.12 python3.12-pip >/dev/null 2>&1; then
            py=python3.12
        elif sudo dnf install -y -q python3.11 python3.11-pip >/dev/null 2>&1; then
            py=python3.11
        else
            echo "ERROR: could not install Python 3.12 or 3.11 with dnf."
            return 1
        fi
    fi

    # Recreate the venv if it was built with a Python that no longer exists.
    if [ -d "$venv" ] && ! "$venv/bin/python" -c "" >/dev/null 2>&1; then
        rm -rf "$venv"
    fi
    if [ ! -d "$venv" ]; then
        echo "Creating Python environment in $venv ..."
        "$py" -m venv "$venv" || return 1
    fi
    # shellcheck disable=SC1091
    source "$venv/bin/activate"

    # Reinstall only when the requirements change (stamp file in the venv).
    local stamp="$venv/.requirements-stamp"
    local want
    want="$(cat "$repo_root/infra/requirements.txt" | md5sum | cut -d' ' -f1)"
    if [ ! -f "$stamp" ] || [ "$(cat "$stamp")" != "$want" ]; then
        echo "Installing Python packages (first time takes a few minutes)..."
        pip install --quiet --no-cache-dir --disable-pip-version-check --upgrade pip || return 1
        pip install --quiet --no-cache-dir --disable-pip-version-check \
            -r "$repo_root/infra/requirements.txt" boto3 python-dotenv || return 1
        echo "$want" > "$stamp"
    fi

    cd "$repo_root" || return 1
    echo
    echo "Ready.  Python: $(python --version 2>&1)   CDK: $(cdk --version 2>/dev/null | cut -d' ' -f1)"
    echo "AWS identity: $(aws sts get-caller-identity --query Arn --output text 2>&1)"
    echo "Region: $AWS_REGION   Folder: $repo_root   Free space in home: $(df -h "$HOME" | awk 'NR==2 {print $4}')"
}

_ciroh_setup

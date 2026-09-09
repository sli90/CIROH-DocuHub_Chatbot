# CIROH DocuHub synchronization system

This folder contains the complete local synchronization system for CIROH
DocuHub. It downloads the current DocuHub repository, detects local and
external-source changes, produces normalized Markdown and RAG JSON, tracks
OpenAI token usage and estimated cost, and can version the changed records in
PostgreSQL.

The React dashboard is an operator interface. The browser never connects to
PostgreSQL directly; it asks the local FastAPI backend to run the pipeline.

## Pipeline behavior

The dashboard's **Run synchronization** action executes these steps in order:

1. Clone or update `CIROH-UA/ciroh_hub`.
2. Detect files changed since the previous synchronization.
3. inspect and download tracked external GitHub README/wiki sources.
4. Merge source content into a normalized `mixed_docs` tree.
5. Generate full artifact/chunk snapshots, incremental deltas, summaries, and
   the token/cost report.
6. Apply the delta to PostgreSQL and generate embeddings.

The confirmation dialog also offers an opt-in **Synchronize GitHub repository
artifacts & chunks** workflow. When selected, the system discovers public repositories in
`CIROH-UA`, stores selected documentation/tutorial files at an immutable commit
SHA, and creates one type-4 artifact with an LLM-generated `summary_data`
description plus RAG chunks per new or changed repository. Obvious chunk types
are classified deterministically; ambiguous documentation sections use the LLM.
This option is off by default.

Repository artifacts and chunks are first written as deterministic JSON
snapshots, then reconciled with active `idArtifactType = 4` rows. The loader
resolves each symbolic `chunk_type_name` against `tblChunkTypes` by name and
creates missing approved type-4 names idempotently. It versions only new or
changed repositories, deactivates removed repositories, embeds inserted rows,
and leaves unchanged rows untouched.

If a command-level step fails, later pipeline steps do not start. Existing
database versions are soft-deactivated rather than deleted, so their artifact
rows and chunks remain available as history. Future deactivations record their
timestamp in `metadata.sync.deactivated_at`; older inactive rows predate this
tracking and do not have a reliable deactivation time.

Other entry points intentionally behave differently:

- `python run_weekly_scan.py` refreshes sources and JSON but does **not** update
  PostgreSQL.
- `python run_weekly_scan.py --include-github-repositories` also refreshes the
  repository artifact/chunk snapshots and LLM descriptions/classifications,
  still without a DB update.
- `python run_full_docuhub_refresh.py` creates and validates a full snapshot but
  does **not** update PostgreSQL. It freezes the validated output into a
  checksum-protected prepared bundle that can be applied later.
- `python run_full_docuhub_refresh.py --include-github-repositories` adds the
  repository artifact/description/chunk stage. It remains JSON-only unless
  `--update-db` is also supplied.
- `python run_full_docuhub_refresh.py --include-github-repositories --update-db`
  freezes the generated data before reconciling and embedding both the type-1
  DocuHub and type-4 repository snapshots. For production, prefer the separate
  prepare/apply commands below so the bundle can be reviewed first.

## Safe two-phase full synchronization

Prepare the complete DocuHub and GitHub-repository synchronization without
touching PostgreSQL:

```bash
python run_full_docuhub_refresh.py --include-github-repositories --use-github-token
```

Repository work is checkpointed after every completed repository. If the
process is interrupted, run the same command again: valid downloaded commit
snapshots are reused, and repositories already stored in the compatible
checkpoint do not repeat their description/chunk LLM calls. The checkpoint is
removed only after the final repository JSON files are written successfully.

After all validation succeeds, the command creates:

```text
local_change_dashboard/prepared_syncs/<sync-id>/
```

That directory contains exact copies of the artifacts, chunks, and generation
reports plus a `manifest.json` with file sizes and SHA-256 hashes. The data files
are not modified during a database attempt. Preview and revalidate the latest
bundle without connecting to PostgreSQL:

```bash
python apply_prepared_sync.py
```

Apply a specific prepared bundle only after it has been reviewed:

```bash
python apply_prepared_sync.py --bundle <sync-id> --execute
```

The apply command performs no GitHub downloads and no summary/classification
calls. It validates every saved hash before connecting, then reconciles type 1
and type 4 by active URL/content fingerprint. Existing versions are
soft-deactivated and replacements are inserted; unchanged versions are left
alone. Each database stage is transactional. If an apply attempt fails, fix the
database or connection issue and run the same command with the same sync ID;
the generation phase does not have to be repeated, and a successfully applied
earlier stage is recognized as unchanged. Attempt reports are retained under
the bundle's `applications/` directory.

## Prerequisites

- Python 3.11 or newer
- Node.js 18 or newer and npm
- Git
- PostgreSQL with the `pgvector` extension available
- An OpenAI API key for summaries and embeddings

A GitHub token is optional for this public-source workflow, but it increases
the GitHub API rate limit.

## 1. Clone and select the branch

```bash
git clone https://github.com/sli90/CIROH-DocuHub_Chatbot.git
cd CIROH-DocuHub_Chatbot
git switch feature/docuhub-sync-system
cd docuhub_sync_system
```

All commands below assume `docuhub_sync_system` is the current directory.
Running the scripts from a different directory is not supported because the
pipeline deliberately keeps its paths relative to this folder.

## 2. Create the Python environment

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

macOS or Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and provide the OpenAI and PostgreSQL values. Never commit `.env`.

## 3. Prepare PostgreSQL

For an empty database, run the included schema as a PostgreSQL user allowed to
create the `vector` extension:

```bash
psql -d ciroh -f "Andres_implementation/schema 1.sql"
```

If an existing application database is used, apply its normal migrations
instead and verify that DocuHub has `idArtifactType = 1`, GitHub Repository has
`idArtifactType = 4`, and the URL uniqueness rule applies only to active rows.
The included schema seeds the required names. During a repository DB run, the
loader also adds any missing approved type-4 chunk names without relying on
environment-specific numeric chunk IDs. The embedding columns must be
`vector(1792)` to match the current processor.

### Azure active-URL migration

Older Azure backups use a global `UNIQUE(url)` constraint, which prevents an
inactive historical row and its active replacement from sharing a URL. After
taking a fresh Azure backup, run the transactional migration through pgAdmin's
Query Tool or `psql`:

```bash
psql "$AZURE_DATABASE_URL" -f "Andres_implementation/migrations/001_active_url_versioning.sql"
```

The migration validates that active URLs are not duplicated, drops only the
legacy `tblartifacts_url_key` constraint, and creates
`idx_artifact_url_active` with `WHERE isActive = TRUE`. If validation or index
creation fails, PostgreSQL rolls the complete migration back.

## 4. Install the frontend

```bash
cd dashboard/frontend
npm ci
cd ../..
```

The frontend uses `http://localhost:8001` by default. To use another API
address, copy `dashboard/frontend/.env.example` to
`dashboard/frontend/.env` and change `VITE_API_BASE`.

## 5. Start the local application

Start the backend from the synchronization-system root:

```bash
python -m uvicorn dashboard.backend.app:app --host 127.0.0.1 --port 8001 --reload
```

In another terminal, with the same repository checked out:

```bash
cd docuhub_sync_system/dashboard/frontend
npm run dev -- --host 127.0.0.1
```

Open <http://127.0.0.1:5173>. The backend health endpoint is
<http://127.0.0.1:8001/api/health>.

Select **Run synchronization** and confirm the operation. A first run is a
baseline run and can take considerably longer because it clones the upstream
repository, summarizes the complete corpus, and creates embeddings.

Leave **Synchronize GitHub repository artifacts & chunks** unchecked to preserve
the existing six-step behavior. Selecting it adds repository generation and
database reconciliation as stages seven and eight, and may make
one OpenAI summary request per new or changed repository plus classification
requests for ambiguous regenerated chunks. Unchanged repository chunks and
descriptions are reused without another OpenAI call.

The repository-only stage can also be invoked directly, but requires an
explicit safety flag:

```bash
python run_github_repository_sync.py --execute
```

Without `--execute`, it exits before making GitHub or OpenAI calls. The direct
command never updates PostgreSQL.

## Generated files and persistence

Generated data is intentionally excluded from Git. On a normal local install,
it remains in this folder between runs. Container or CI deployments must mount
durable storage for the following state:

- `ciroh_hub_sync.json`
- `local_change_dashboard/external_repos.json`
- `local_change_dashboard/external_repo_files/`
- `local_change_dashboard/mixed_docs/`
- `local_change_dashboard/mixed_docs_manifest.json`
- `local_change_dashboard/github_repository_sync.json`
- `local_change_dashboard/github_repository_corpus/`
- `dashboard/formated_files/_hashes.json`
- `dashboard/formated_files/artifacts.json`
- `dashboard/formated_files/content_chunks.json`
- `dashboard/formated_files/coderepo_artifacts.json`
- `dashboard/formated_files/coderepo_chunks.json`
- `dashboard/formated_files/github_repository_generation_report.json`
- `dashboard/formated_files/github_repository_db_update_result.json`
- `dashboard/formated_files/synchronization_reports/`

`_hashes.json` is required to detect updates and deletions. The previous
`artifacts.json` is also used to carry summaries forward for unchanged pages.
Likewise, `github_repository_sync.json`, `coderepo_artifacts.json`,
`coderepo_chunks.json`, and the repository corpus preserve stable repository
and chunk IDs and allow unchanged descriptions/chunks to be reused without
another OpenAI call.
If this state is discarded on every run, the system can classify the corpus as
new, repeat OpenAI work, and fail to identify documents deleted since the last
run.

The mutable working snapshots are overwritten. Prepared bundles, delta files,
and synchronization/application reports are retained for recovery and audit
and are not automatically pruned. Establish a retention and backup policy for
long-running installations rather than committing these generated files to
Git.

## Output order

Artifacts are emitted deterministically by DocuHub section, hierarchy, and
path. Chunks follow artifact and heading order. Generated numeric source IDs
can shift when documents are inserted earlier in that order, so URLs—not JSON
array positions or generated IDs—should be treated as stable identities.

GitHub repository artifacts are emitted alphabetically by `full_name`.
Previously assigned repository artifact IDs are preserved by `full_name`; new
repositories receive the next available ID. Old immutable commit snapshots are
kept in the local corpus, while removed repositories are omitted from the new
JSON and their active database rows are soft-deactivated during reconciliation.
Repository chunks follow repository, source-file, and section order. Chunks for
unchanged commit SHAs retain their IDs; chunks rebuilt for an updated repository
receive new, non-recycled IDs so parent references remain unambiguous.

## Token and cost accounting

Each synchronization report separates DocuHub summarization, repository
summarization, repository chunk classification, and embedding usage. It records
input, cached-input, output, reasoning, and total tokens when returned by the
OpenAI API, plus an estimated USD cost and pricing source date. Pricing can be
overridden with the optional variables shown in `.env.example`.

The latest report is written to:

```text
dashboard/formated_files/synchronization_report.json
```

Historical reports are written under:

```text
dashboard/formated_files/synchronization_reports/
```

A fresh clone also includes a few lightweight, sanitized run summaries under
`dashboard/bootstrap/synchronization_reports/`. They let teammates see the
existing dashboard history without receiving a database dump, artifact/chunk
payloads, embeddings, prepared bundles, or credentials. The backend merges the
bundled summaries with locally generated reports by `sync_id`; the local report
wins when both sources contain the same run. Reading this history does not
connect to or update PostgreSQL or Azure.

## Verification

Run the Python tests from this folder:

```bash
python -m unittest discover -s . -p "test_*.py"
python -m unittest discover -s dashboard -p "test_*.py"
```

Tests that inspect upstream DocuHub content are skipped until the first
synchronization has created the local `ciroh_hub` checkout.

Build the frontend:

```bash
cd dashboard/frontend
npm run build
```

## Security and operational notes

- Never commit `.env`, database dumps, generated JSON, downloaded external
  documents, logs, or OpenAI/GitHub credentials.
- Without `DASHBOARD_OPERATOR_TOKEN`, pipeline execution is restricted to
  loopback clients. Set a strong token before exposing the API beyond the local
  machine.
- When a token is configured, the frontend or API caller must provide it as
  `X-CIROH-Operator-Key` or `Authorization: Bearer <token>`.
- Database versions are retained with `isActive = FALSE`; plan a separate data
  retention policy if indefinite history is not required.
- Each database synchronization runs as one transaction. A failed insert,
  chunk mapping, or embedding write rolls back the corresponding deactivation
  and replacement operations together.
- Keep the prepared bundle until the database update has been verified and
  backed up. Its manifest detects accidental changes before any retry.

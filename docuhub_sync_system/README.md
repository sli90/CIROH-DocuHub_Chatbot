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

If a command-level step fails, later pipeline steps do not start. Existing
database versions are soft-deactivated rather than deleted, so their artifact
rows and chunks remain available as history.

Other entry points intentionally behave differently:

- `python run_weekly_scan.py` refreshes sources and JSON but does **not** update
  PostgreSQL.
- `python run_full_docuhub_refresh.py` creates and validates a full snapshot but
  does **not** update PostgreSQL unless `--update-db` is provided.
- `python run_full_docuhub_refresh.py --update-db` deactivates the active
  DocuHub set and loads the validated full snapshot.

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

Then seed the names expected by the delta processor:

```sql
INSERT INTO tblartifacttypes (idartifacttype, typename)
VALUES (1, 'DocuHub')
ON CONFLICT DO NOTHING;

INSERT INTO tblchunktypes (idartifacttype, typename)
VALUES
  (1, 'Section'),
  (1, 'Subsection'),
  (1, 'Subsubsection')
ON CONFLICT DO NOTHING;
```

If an existing application database is used, apply its normal migrations
instead and verify that DocuHub has `idArtifactType = 1` and the three chunk
types above exist. The embedding columns must be `vector(1792)` to match the
current processor.

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

## Generated files and persistence

Generated data is intentionally excluded from Git. On a normal local install,
it remains in this folder between runs. Container or CI deployments must mount
durable storage for the following state:

- `ciroh_hub_sync.json`
- `local_change_dashboard/external_repos.json`
- `local_change_dashboard/external_repo_files/`
- `local_change_dashboard/mixed_docs/`
- `local_change_dashboard/mixed_docs_manifest.json`
- `dashboard/formated_files/_hashes.json`
- `dashboard/formated_files/artifacts.json`
- `dashboard/formated_files/content_chunks.json`
- `dashboard/formated_files/synchronization_reports/`

`_hashes.json` is required to detect updates and deletions. The previous
`artifacts.json` is also used to carry summaries forward for unchanged pages.
If this state is discarded on every run, the system can classify the corpus as
new, repeat OpenAI work, and fail to identify documents deleted since the last
run.

Current full snapshots are overwritten. Delta and synchronization reports are
timestamped for audit history and are not automatically pruned. Establish a
retention policy for long-running installations rather than committing these
files to Git.

## Output order

Artifacts are emitted deterministically by DocuHub section, hierarchy, and
path. Chunks follow artifact and heading order. Generated numeric source IDs
can shift when documents are inserted earlier in that order, so URLs—not JSON
array positions or generated IDs—should be treated as stable identities.

## Token and cost accounting

Each synchronization report separates summarization and embedding usage and
records input, cached-input, output, reasoning, and total tokens when returned
by the OpenAI API. It also records an estimated USD cost and the pricing source
date. Pricing can be overridden with the optional variables shown in
`.env.example`.

The latest report is written to:

```text
dashboard/formated_files/synchronization_report.json
```

Historical reports are written under:

```text
dashboard/formated_files/synchronization_reports/
```

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
- The current database helper commits its operations in batches. Run database
  backups and monitoring for production schedules because a late failure is
  not a single all-or-nothing transaction.

# CIROH DocuHub synchronization system

## 1. Introduction

The synchronization system keeps the CIROH chatbot content aligned with three
sources: CIROH Hub documentation, CIROH GitHub repositories, and HydroShare
Research Portal resources. It detects new, modified, and removed content;
generates artifacts, chunks, summaries, and embeddings; and records token usage
and estimated OpenAI cost.

Database records are versioned rather than deleted. When content changes, the
previous artifact is marked inactive and its historical chunks are preserved.

## 2. Synchronize the three sources

Configure `docuhub_sync_system/.env` and activate the Python environment.

### Option 1: Dashboard (recommended)

Start the application from `docuhub_sync_system`:

```bash
# Terminal 1: backend
python -m uvicorn dashboard.backend.app:app --host 127.0.0.1 --port 8001 --reload

# Terminal 2: frontend
cd dashboard/frontend
npm run dev -- --host 127.0.0.1
```

Open <http://127.0.0.1:5173> and select **Run synchronization**. CIROH Hub is
always included; select GitHub repositories and HydroShare when you want to
synchronize those sources too. The dashboard runs the selected synchronization
and updates the configured database in the same workflow.

### Option 2: Command line

Run the appropriate command from `docuhub_sync_system`.

#### CIROH Hub

```bash
python run_full_docuhub_refresh.py
```

This synchronizes CIROH Hub documentation and linked external content, then
creates a reviewable prepared bundle. It does not update the database unless
`--update-db` is explicitly supplied.

#### GitHub repositories

```bash
python run_github_repository_sync.py --execute
```

This creates or updates the GitHub repository artifacts, descriptions, and
chunks. It does not update the database.

#### HydroShare

```bash
python run_hydroshare_sync.py
```

This creates or updates HydroShare artifacts, chunks, and Research Portal
memberships. Public HydroShare resources do not require an API key. This
command does not update the database.

#### Prepare all three sources together

```bash
python run_full_docuhub_refresh.py \
  --include-github-repositories \
  --include-hydroshare-resources \
  --use-github-token
```

The command prints a synchronization ID and saves the validated snapshot under
`local_change_dashboard/prepared_syncs/<sync-id>/`.

## 3. Update the database

### Option 1: Dashboard (recommended)

First verify that `.env` points to the intended database, uses
`POSTGRES_SCHEMA=CIROH_AIBot`, and that a fresh database backup is available.
In the dashboard, select the sources you want and run the synchronization. The
dashboard generates the selected snapshots and updates the database
automatically. Previous artifact versions are marked inactive rather than
deleted.

### Option 2: Reviewable command line

For an important Azure/production update, the prepared-bundle workflow lets
you inspect the exact data before applying it:

1. Review and validate the prepared bundle without connecting to PostgreSQL:

   ```bash
   python apply_prepared_sync.py --bundle <sync-id>
   ```

2. Verify `.env` again and take a fresh backup of the target database.
3. Apply the reviewed bundle:

   ```bash
   python apply_prepared_sync.py --bundle <sync-id> --execute
   ```

The apply command validates the saved bundle before connecting. Unchanged rows
remain untouched; new or modified content receives a new active version, and
previous versions are marked inactive instead of being deleted.

For complete installation, configuration, migration, dashboard, and recovery
instructions, see [`docuhub_sync_system/README.md`](docuhub_sync_system/README.md).

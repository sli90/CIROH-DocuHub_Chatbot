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

Configure `docuhub_sync_system/.env`, activate the Python environment, and run
these commands from `docuhub_sync_system`.

### CIROH Hub

```bash
python run_full_docuhub_refresh.py
```

This synchronizes CIROH Hub documentation and linked external content, then
creates a reviewable prepared bundle. It does not update the database unless
`--update-db` is explicitly supplied.

### GitHub repositories

```bash
python run_github_repository_sync.py --execute
```

This creates or updates the GitHub repository artifacts, descriptions, and
chunks. It does not update the database.

### HydroShare

```bash
python run_hydroshare_sync.py
```

This creates or updates HydroShare artifacts, chunks, and Research Portal
memberships. Public HydroShare resources do not require an API key. This
command does not update the database.

### Prepare all three sources together

```bash
python run_full_docuhub_refresh.py \
  --include-github-repositories \
  --include-hydroshare-resources \
  --use-github-token
```

The command prints a synchronization ID and saves the validated snapshot under
`local_change_dashboard/prepared_syncs/<sync-id>/`.

## 3. Update the database

1. Review and validate the prepared bundle without connecting to PostgreSQL:

   ```bash
   python apply_prepared_sync.py --bundle <sync-id>
   ```

2. Verify that `.env` points to the intended database and uses
   `POSTGRES_SCHEMA=CIROH_AIBot`.
3. Take and verify a fresh backup of the target database.
4. Apply the reviewed bundle:

   ```bash
   python apply_prepared_sync.py --bundle <sync-id> --execute
   ```

The apply command validates the saved bundle before connecting. Unchanged rows
remain untouched; new or modified content receives a new active version, and
previous versions are marked inactive instead of being deleted.

For complete installation, configuration, migration, dashboard, and recovery
instructions, see [`docuhub_sync_system/README.md`](docuhub_sync_system/README.md).

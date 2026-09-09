# Bundled synchronization history

This directory contains small, sanitized summaries of earlier synchronization
runs so a fresh local dashboard can display useful history immediately.

These files are display-only. They do not contain artifacts, chunks,
embeddings, database rows, credentials, connection strings, or prepared-sync
payloads, and loading them never connects to or updates a database.

Runtime reports remain under `dashboard/formated_files/synchronization_reports`.
The backend merges both sources by `sync_id`; a local runtime report takes
precedence over a bundled report with the same ID.

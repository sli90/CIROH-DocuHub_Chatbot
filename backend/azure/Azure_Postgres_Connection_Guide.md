### Azure PostgreSQL (Flexible Server) — Connection and Usage Guide

This document explains how to connect to, query, and upload data into the Azure PostgreSQL (Flexible Server) instance provisioned for CIROH.

---

## Quick facts

- **Server name**: `ciroh-website`
- **FQDN (host)**: `ciroh-website.postgres.database.azure.com`
- **Port**: `5432`
- **Engine**: PostgreSQL `17`
- **Region**: `eastus`
- **Admin user**: `CIROH_ADM`
- **Default database**: `postgres` (you can create and use project-specific databases)
- **Public network access**: Enabled
- **Firewall allowlist (example)**: `130.160.194.9` (from the deployment at the time of writing)

All values above are sourced from `backend/azure/Deployment_Docs/deployment.json` in this repo.

> Important
> - Password is not stored in plain text in the deployment file (it appears as a secure string). Retrieve it from your secret manager, Azure Portal, or team lead.
> - Azure Flexible Server requires SSL. Use `sslmode=require` in all connections.

---

## Prerequisites

- psql installed (from PostgreSQL client tools) or a GUI (Azure Data Studio, DBeaver, pgAdmin)
- Azure CLI (optional but recommended): `az --version`
- Network access: your client IP must be allowed through the server firewall

---

## Ensure your IP is allowed (Firewall)

If you cannot connect, your public IP may not be allowed yet.

Using Azure Portal (UI):
- Navigate to Azure Database for PostgreSQL Flexible Server → `ciroh-website` → Networking → Firewall rules
- Add your IP address with start = end = your public IP → Save

Using Azure CLI:

```bash
az login
az account set --subscription <SUBSCRIPTION_ID>
az postgres flexible-server firewall-rule create \
  --resource-group rg-aiinstitute-storage \
  --name ciroh-website \
  --rule-name allow-my-ip \
  --start-ip-address <YOUR_PUBLIC_IP> \
  --end-ip-address <YOUR_PUBLIC_IP>
```

Replace `<YOUR_PUBLIC_IP>` with your actual IP (e.g., `203.0.113.10`).

---

## Connection strings

General DSN parameters:
- host: `ciroh-website.postgres.database.azure.com`
- port: `5432`
- dbname: `postgres` (or another database you create)
- user: `CIROH_ADM`
- password: `<your password>`
- sslmode: `require`

### psql (CLI)

```bash
psql "host=ciroh-website.postgres.database.azure.com port=5432 dbname=postgres user=CIROH_ADM sslmode=require"
```

You will be prompted for the password. To supply inline (not recommended):

```bash
PGPASSWORD="<PASSWORD>" psql "host=ciroh-website.postgres.database.azure.com port=5432 dbname=postgres user=CIROH_ADM sslmode=require"
```

Windows PowerShell:

```powershell
$Env:PGPASSWORD = "<PASSWORD>"
psql "host=ciroh-website.postgres.database.azure.com;port=5432;dbname=postgres;user=CIROH_ADM;sslmode=require"
```

### libpq connection URI

```bash
postgresql://CIROH_ADM:<PASSWORD>@ciroh-website.postgres.database.azure.com:5432/postgres?sslmode=require
```

### Python (psycopg2)

```python
import psycopg2

conn = psycopg2.connect(
    host="ciroh-website.postgres.database.azure.com",
    port=5432,
    dbname="postgres",
    user="CIROH_ADM",
    password="<PASSWORD>",
    sslmode="require",
)

with conn, conn.cursor() as cur:
    cur.execute("SELECT version();")
    print(cur.fetchone())
```

### Node.js (pg)

```javascript
import { Client } from "pg";

const client = new Client({
  connectionString: "postgresql://CIROH_ADM:<PASSWORD>@ciroh-website.postgres.database.azure.com:5432/postgres?sslmode=require",
});

await client.connect();
const { rows } = await client.query("SELECT now() as now");
console.log(rows[0]);
await client.end();
```

### SQLAlchemy (Python)

```python
from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://CIROH_ADM:<PASSWORD>@ciroh-website.postgres.database.azure.com:5432/postgres?sslmode=require",
    pool_pre_ping=True,
)

with engine.begin() as conn:
    conn.execute(text("SELECT 1"))
```

---

## First-time admin setup (recommended)

1) Create a project database and a standard user:

```sql
-- connect as admin to database: postgres
CREATE DATABASE ciroh;
\c ciroh

-- create a role for app usage
CREATE ROLE ciroh_rw LOGIN PASSWORD '<STRONG_PASSWORD>';
GRANT CONNECT ON DATABASE ciroh TO ciroh_rw;

-- default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ciroh_rw;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO ciroh_rw;
```

2) Optionally, restrict admin use to maintenance and use the new role for applications.

---

## Basic querying

Using psql:

```sql
\c ciroh
CREATE TABLE demo_sites (
  site_id   SERIAL PRIMARY KEY,
  name      TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO demo_sites (name) VALUES ('alpha'), ('beta');

SELECT * FROM demo_sites ORDER BY site_id;
```

---

## Uploading data

### CSV import with psql (client-side)

`\copy` runs on your client and is usually easiest for CSV files.

```bash
psql "host=ciroh-website.postgres.database.azure.com port=5432 dbname=ciroh user=CIROH_ADM sslmode=require" \
  -c "CREATE TABLE IF NOT EXISTS measurements (ts timestamptz, gage_id text, value double precision);"

psql "host=ciroh-website.postgres.database.azure.com port=5432 dbname=ciroh user=CIROH_ADM sslmode=require" \
  -c "\copy measurements (ts, gage_id, value) FROM 'data.csv' WITH (FORMAT csv, HEADER true)"
```

If you see permission errors, grant rights to your non-admin role or run as admin and then `GRANT` permissions.

### Python bulk load (psycopg `copy_expert`)

```python
import psycopg2

conn = psycopg2.connect(
    host="ciroh-website.postgres.database.azure.com",
    port=5432,
    dbname="ciroh",
    user="CIROH_ADM",
    password="<PASSWORD>",
    sslmode="require",
)

with conn, conn.cursor() as cur, open("data.csv", "r", encoding="utf-8") as f:
    cur.copy_expert(
        "COPY measurements (ts, gage_id, value) FROM STDIN WITH (FORMAT csv, HEADER true)",
        f,
    )
```

### pandas → SQLAlchemy

```python
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg2://CIROH_ADM:<PASSWORD>@ciroh-website.postgres.database.azure.com:5432/ciroh?sslmode=require"
)

df = pd.read_csv("data.csv")
df.to_sql("measurements", engine, if_exists="append", index=False)
```

### Restoring from a dump

For a custom-format dump (`.dump`):

```bash
pg_restore \
  --host=ciroh-website.postgres.database.azure.com \
  --port=5432 \
  --username=CIROH_ADM \
  --dbname=ciroh \
  --no-owner --no-privileges \
  --format=custom \
  path/to/archive.dump
```

For a plain SQL file:

```bash
psql "host=ciroh-website.postgres.database.azure.com port=5432 dbname=ciroh user=CIROH_ADM sslmode=require" -f dump.sql
```

---

## Managing credentials securely

Environment variables (recommended):

```bash
export AZURE_PGHOST=ciroh-website.postgres.database.azure.com
export AZURE_PGPORT=5432
export AZURE_PGUSER=CIROH_ADM
export AZURE_PGDB=ciroh
export AZURE_PGPASSWORD=<PASSWORD>

psql "host=$AZURE_PGHOST port=$AZURE_PGPORT dbname=$AZURE_PGDB user=$AZURE_PGUSER sslmode=require"
```

`.pgpass` (libpq):

```
ciroh-website.postgres.database.azure.com:5432:*:CIROH_ADM:<PASSWORD>
```

Windows path: `%APPDATA%\postgresql\pgpass.conf`.

Rotate passwords periodically and restrict sharing of admin credentials.

---

## Troubleshooting

- Connection refused or timeout: ensure your IP is allowlisted and outbound network allows 5432.
- `no pg_hba.conf entry` / auth failures: verify user, db, password; Azure uses server-level firewall, not local pg_hba.
- SSL errors: include `sslmode=require` and ensure client supports TLS 1.2+.
- Permission denied on table/sequence: connect as admin, grant privileges to your role, or adjust default privileges.

---

## Reference

- Resource group: `rg-aiinstitute-storage`
- Server: `ciroh-website` (`ciroh-website.postgres.database.azure.com`)
- Admin: `CIROH_ADM`
- Version: `17`
- Example allowed IP from deployment: `130.160.194.9`



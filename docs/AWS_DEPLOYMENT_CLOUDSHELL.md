# Deploying with AWS CloudShell (no access portal, no access keys)

Use this guide if you can sign in to the **AWS console** in a browser, but
you **can't** use the AWS CLI from your laptop (no IAM Identity Center
"start URL", no access keys, e.g. because of university policy).

You still don't have to click together 40+ resources by hand. **AWS
CloudShell** is a Linux terminal *inside the AWS console*. It is already
signed in as you (same permissions as your console session), and it comes
with the AWS CLI, the CDK CLI, Node.js, Python and git. Your laptop does
the parts that need the Azure database, CloudShell does the parts that need
AWS, and a single zip file carries the work between them.

```
Your laptop (no AWS needed)                 AWS console -> CloudShell (no laptop credentials needed)
─────────────────────────────               ───────────────────────────────────────────────────────
build website + export Azure corpus  ──zip──>  deploy with CDK -> load corpus into Aurora -> test
```

**Time:** ~2 hours the first time, mostly waiting. **Cost while testing:**
~$8-15/month idle plus ~$0.003 per question (Part 9 deletes everything).

Background on what gets built and why: [AWS_DEPLOYMENT.md](./AWS_DEPLOYMENT.md)
("What you are building") and [AWS_ARCHITECTURE.md](./AWS_ARCHITECTURE.md).

---

## Part 1 - On your laptop: make the upload file (~10 minutes)

You need the Azure DB credentials in the repo-root `.env` file (the same
ones local development uses: `POSTGRES_HOST`, `POSTGRES_DB`,
`POSTGRES_SCHEMA=CIROH_AIBot`, `POSTGRES_USER`, `POSTGRES_PASSWORD`).

First, open [`infra/cdk.json`](../infra/cdk.json) in your editor and put your
email in `"budget_alert_email": "you@crimson.ua.edu",` for cost and error
alerts. Setting it here, before zipping, means every deploy keeps it.

Then in PowerShell, from the repo root:

```bash
.venv\Scripts\Activate.ps1
```

```bash
pip install -r backend/requirements.txt
```

```bash
python scripts/make_cloudshell_bundle.py
```

This does three things, all without AWS:

1. Builds the website (`frontend/dist`).
2. Exports every artifact and chunk from the Azure database to
   `backend/database/corpus_export.json.gz`. It should report several
   hundred artifacts and several thousand chunks.
3. Zips the code plus both outputs into **`ciroh-cloudshell.zip`** in the
   repo root, typically a few MB. Your `.env` and passwords are never put in
   the zip.

If step 2 fails to connect, your `.env` values are wrong or your IP isn't
allowed on the Azure database firewall. That's the same thing local
development needs.

---

## Part 2 - Sign in and look around (console)

1. Sign in to the AWS console the way your admin set up for you. If you
   don't know how you're supposed to sign in, ask them. Everything below
   happens inside the console.
2. **Region:** top-right corner, click the region name and choose **US East
   (N. Virginia) us-east-1**. Keep it there for this whole guide. If a
   resource seems to "disappear", check the region first.
3. **Account ID:** click your account name (top-right) and note the 12-digit
   Account ID.
4. **MFA:** if you haven't yet: account name (top-right) → **Security
   credentials** → **Assign MFA device**. If you sign in through your
   university's login page, MFA is handled there instead.
5. **Permission sanity check:** type `IAM` in the top search bar, open it,
   click **Roles**. A list (not a red "not authorized" box) is a good sign.
   Deploying needs broad permissions (AdministratorAccess on the
   subaccount); see [the message to your admin](#if-your-admin-asks-what-you-need)
   at the end.

---

## Part 3 - Turn on the Bedrock models (console, ~5 minutes)

Claude needs a one-time setup per account, done by a person:

1. Search **Amazon Bedrock**, open it (region N. Virginia).
2. Left menu → **Model catalog** → search **Claude Haiku 4.5** → open it.
3. If it asks you to **submit use case details**, do it. Company:
   *University of Alabama / CIROH*. Use case: *"Retrieval-augmented Q&A
   chatbot over CIROH hydrology documentation for researchers."* Wait ~5
   minutes.
4. Click **Open in playground** (or left menu → **Playgrounds → Chat**,
   choose Claude Haiku 4.5), type `hello`, send. Getting a reply completes
   the setup.

Titan Text Embeddings V2 needs nothing.

---

## Part 4 - Open CloudShell and upload (~10 minutes)

### 4.1 Open it

In the console's top bar, click the **CloudShell icon**: a small square
with `>_`, to the left of the bell icon. (Or search `CloudShell`.) A
terminal panel opens at the bottom, or in its own tab. The first launch
takes a minute; you're ready when you see a prompt like:

```
[cloudshell-user@ip-10-0-12-34 ~]$
```

CloudShell may open in any region. The setup script in 4.3 points
everything at us-east-1 anyway. If you see **"Unable to create the
environment"**, click **Open a tab → us-east-2** (or another region it
offers). If no region works, see
[AWS_PERMISSIONS.md](./AWS_PERMISSIONS.md#about-unable-to-create-the-environment-in-cloudshell).
Don't choose "Create a VPC environment".

**Two things to know about CloudShell:**

- **It closes after 20-30 minutes without keyboard/mouse input**, even if
  a command is running. During long steps (deploy, data load), click into
  the terminal and press Enter every ~10 minutes. If it does close,
  nothing is lost: see "If CloudShell disconnects" in Part 8.
- **Only your home folder is kept between sessions** (1 GB). Installed
  system packages disappear, which is why Part 4.3 is re-run each session.

Paste into CloudShell with **Ctrl+Shift+V** (or right-click → Paste).

### 4.2 Upload and unzip

1. In the CloudShell window, click **Actions** (top-right of the terminal)
   → **Upload file** → choose `ciroh-cloudshell.zip` from your repo root →
   **Upload**.
2. Unzip it:

   ```bash
   unzip -o ciroh-cloudshell.zip
   ```

   This creates a folder `ciroh/` in your home directory.

### 4.3 Set up the session (every time you open CloudShell)

```bash
cd ~/ciroh && source scripts/cloudshell_setup.sh
```

The first time it installs Python 3.12 and the CDK libraries (~3-5
minutes); later sessions take ~30 seconds. It ends with something like:

```
Ready.  Python: Python 3.12.x   CDK: 2.xxxx.x
AWS identity: arn:aws:sts::123456789012:assumed-role/...
Region: us-east-1   Folder: /home/cloudshell-user/ciroh   Free space in home: 700M
```

Note it's `source`, not `bash`. Your prompt now starts with `(.ciroh-venv)`.

### 4.4 Confirm Bedrock access

```bash
python scripts/check_bedrock_access.py
```

Both lines should say `[OK]`. If not, redo Part 3. If the error mentions
an SCP, organization or Marketplace, send it to your admin.

---

## Part 5 - Deploy the infrastructure (~20-25 minutes)

### 5.1 Check your alert email

```bash
grep budget_alert_email ~/ciroh/infra/cdk.json
```

If it still shows `""` (you skipped that part of Part 1), set it here.
Replace the address with yours:

```bash
sed -i 's/"budget_alert_email": ""/"budget_alert_email": "you@crimson.ua.edu"/' ~/ciroh/infra/cdk.json
```

### 5.2 Bootstrap (once per account)

```bash
cd ~/ciroh/infra && cdk bootstrap
```

Ends with `Environment aws://<account>/us-east-1 bootstrapped`.

### 5.3 Deploy

```bash
cdk deploy CirohStack
```

- It first builds the Lambda package ("Bundling Lambda package with local
  pip"), then lists the security changes and asks `Do you wish to deploy
  these changes (y/n)?`. Type **y** and press Enter.
- Then it takes **~15-25 minutes** (Aurora and CloudFront are the slow
  parts). **Press Enter in the terminal every ~10 minutes** so CloudShell
  doesn't time out.
- Watch it live in a second browser tab: **CloudFormation → Stacks →
  CirohStack → Events**. If something fails, the **oldest** red
  `CREATE_FAILED` event is the real reason.

When it finishes, it prints the **Outputs**. The one you care about:

```
CirohStack.FrontendUrl = https://dxxxxxxxxxxxxx.cloudfront.net
```

The website is already published, since the zip contained the built site.
It can't answer questions until Part 6 loads the data.

**Check your email** for "AWS Notification - Subscription Confirmation" and
click **Confirm subscription**.

**Deploy blocked by your organization?** If the failure mentions
`AWS::Budgets::Budget` and "explicit deny", run:

```bash
cdk deploy CirohStack -c enable_budgets=false
```

(See the Troubleshooting table in AWS_DEPLOYMENT.md for other errors.)

---

## Part 6 - Load the knowledge base into Aurora (~15-40 minutes)

Everything reads the corpus file you exported in Part 1, and the Aurora
details from the deployed stack, automatically.

**No Azure access?** Then there's no exported corpus file. Rebuild the
corpus from the source files in the repo instead. This does the same thing
`PopulateDB.ipynb` did to fill Azure, and generates the CIROH Hub page
summaries with Bedrock (about $2, one time). Then continue with step 1
below:

```bash
cd ~/ciroh/backend/database && python build_corpus_from_json.py
```

```bash
cd ~/ciroh/backend/database
```

1. Create the tables (the first statement waits ~15s for the database to
   wake up):

   ```bash
   python migrate_to_bedrock.py --apply-schema
   ```

2. Smoke test with 20 artifacts:

   ```bash
   python migrate_to_bedrock.py --limit 20
   ```

3. Load everything. Already-loaded rows are skipped. **Press Enter every ~10
   minutes.** If it's interrupted, just run the same command again:

   ```bash
   python migrate_to_bedrock.py
   ```

4. Check it:

   ```bash
   python migrate_to_bedrock.py --validate --sample-question "What is NextGen In A Box?" --sample-question "How do I get access to CIROH cloud computing resources?"
   ```

   Good result: `Orphan chunks: 0`, `Artifacts with NULL embedding: 0`, and
   three relevant titles per question with distances around **0.3-0.6**.

*See the data in the console:* **Aurora and RDS → Query editor** → choose
`ciroh-docuhub-aurora` → **Connect with a Secrets Manager ARN** → paste the
`AuroraSecretArn` (shown under **CloudFormation → CirohStack → Outputs**) →
database `ciroh` → run `SELECT title, url FROM tblartifacts LIMIT 10;`

---

## Part 7 - Test it

In CloudShell:

```bash
cd ~/ciroh && python scripts/smoke_test.py
```

Expect `[OK]` on the real questions (each well under 20s) and the
off-topic question refused. Then open your **FrontendUrl** in the browser,
click the chat icon, and ask a few questions.

Where to look in the console:

- **CloudWatch → Log groups → `/ciroh-docuhub/ciroh-docuhub-ask`**: one
  `TELEMETRY` line per question (route, tokens, estimated cost) and any
  errors.
- **Lambda → ciroh-docuhub-ask → Monitor**: requests, duration, errors.
- **Billing and Cost Management → Cost Explorer** (a day later): real
  Bedrock spend.

After ~5 idle minutes the database sleeps. The first question afterwards
may take ~15s longer, or fail once; ask again. Opening the chat panel
already starts waking it.

---

## Part 8 - Everyday use

### If CloudShell disconnects during a deploy

The deploy keeps running in AWS without you. Reopen CloudShell, run
`cd ~/ciroh && source scripts/cloudshell_setup.sh`, and watch
**CloudFormation → CirohStack**:

- `CREATE_COMPLETE` / `UPDATE_COMPLETE`: done. Run
  `cd infra && cdk deploy CirohStack` once to print the outputs; it finishes
  quickly with no changes.
- `..._IN_PROGRESS`: wait, refresh.
- `ROLLBACK_COMPLETE`: it failed. Read the oldest `CREATE_FAILED` event,
  fix it, click **Delete** on the stack, then deploy again.

If it disconnects during the data load, just rerun the same
`migrate_to_bedrock.py` command. It resumes.

### Changing code later

1. Laptop: edit the code, then run
   `python scripts/make_cloudshell_bundle.py --skip-corpus`.
   Leave out `--skip-corpus` only if the Azure data changed.
2. CloudShell: **Actions → Upload file** → `ciroh-cloudshell.zip`, then:

   ```bash
   cd ~ && unzip -o ciroh-cloudshell.zip && cd ~/ciroh && source scripts/cloudshell_setup.sh
   ```

   ```bash
   cd ~/ciroh/infra && cdk deploy CirohStack
   ```

   (`unzip -o` replaces the CloudShell copy with your laptop's files, so make
   config changes like `infra/cdk.json` on the laptop.)

### Settings you may want to change

Edit `infra/cdk.json` (on your laptop, then re-bundle), then deploy:

- `retrieval_similarity_threshold` (default 0.7): raise it if real
  questions get "only answers questions about CIROH" refusals. See
  GUARDRAILS_AND_COST.md.
- `aurora_min_acu`: set to `0.5` to remove the wake-up delay
  (~$43/month more).

### Troubleshooting

CloudShell-specific issues are below. Everything else, like AWS errors and
chatbot behavior, is in the Troubleshooting table in
[AWS_DEPLOYMENT.md, Part 9](./AWS_DEPLOYMENT.md#part-9---troubleshooting).

| Symptom | Fix |
|---|---|
| `python: command not found` / packages missing after reopening CloudShell | Run `cd ~/ciroh && source scripts/cloudshell_setup.sh` (every session). |
| `No space left on device` | `rm -rf ~/ciroh/infra/cdk.out ~/.cache ~/ciroh-cloudshell.zip`, then retry. `df -h ~` shows free space. |
| `This CDK CLI is not compatible with the CDK library` (cloud assembly schema) | Use the newest CLI for that command: `npx aws-cdk@latest deploy CirohStack`. |
| Pasting doesn't work | Use Ctrl+Shift+V, or right-click → Paste. |
| `Unable to locate credentials` | Your console session expired. Refresh the console page, reopen CloudShell, re-run the setup line. |

---

## Part 9 - Delete everything

```bash
cd ~/ciroh && source scripts/cloudshell_setup.sh && cd infra && cdk destroy CirohStack
```

Type `y`, and keep the tab active while it runs (~10-20 minutes). This
deletes the database and its data too (the default `env_name` is `dev`).

---

## If your admin asks what you need

> To deploy the CIROH chatbot I'll use AWS CloudShell from the console (no
> access keys or portal URL needed). My console role needs:
> - **AdministratorAccess** on the subaccount (CDK creates IAM roles, a VPC,
>   Aurora, Lambda, API Gateway, CloudFront, WAF, Bedrock Guardrails,
>   Budgets, SNS, CloudWatch)
> - **CloudShell** allowed
> - **Bedrock** allowed in us-east-1, us-east-2 and us-west-2 (Claude Haiku
>   4.5 uses the US cross-region inference profile)
> - **AWS Marketplace** subscribe allowed (one-time Anthropic model
>   enablement)
> - **AWS Budgets** allowed. Optional: I can turn Budgets off if policy
>   requires.

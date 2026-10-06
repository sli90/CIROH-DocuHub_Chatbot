# Deploying the CIROH DocuHub Chatbot to AWS

A step-by-step guide for someone who has **never used AWS before** and has
just been given an AWS (sub)account. It takes you from "I can log in to the
AWS console" to "the chatbot is live on a public URL and answering questions
from Bedrock + Aurora".

> **Can't use the AWS CLI from your laptop** (no access portal URL, no
> access keys)? Follow **[AWS_DEPLOYMENT_CLOUDSHELL.md](./AWS_DEPLOYMENT_CLOUDSHELL.md)**
> instead. It does the same deployment from AWS CloudShell inside the
> console.

- Architecture and design reasoning: [AWS_ARCHITECTURE.md](./AWS_ARCHITECTURE.md)
- Guardrail and cost tuning: [GUARDRAILS_AND_COST.md](./GUARDRAILS_AND_COST.md)

**Time:** about 2 hours the first time, most of it waiting (deploy ~20 min,
corpus re-embed ~15-40 min). **Cost while testing:** roughly $8-15/month idle
(WAF $7, the rest pennies), plus about $0.003 per question. Part 10 shows how
to delete everything.

---

## What you are building

```
Browser ──> CloudFront (+ WAF) ──┬── /            -> S3 bucket (the React app)
                                 └── /ask, /telemetry -> API Gateway -> Lambda (FastAPI)
                                                                         ├─> Bedrock: Claude Haiku 4.5 + Titan Embeddings
                                                                         └─> Aurora Serverless v2 (Postgres + pgvector) via the RDS Data API
```

Everything is created by **one command** (`cdk deploy`) from the code in
[`infra/`](../infra/). You will use the AWS **console** (the website) to sign
in, turn on model access, and look at what got created. You will use a
**terminal** (PowerShell) to run the deploy.

A few words you will see everywhere:

| Term | Meaning |
|---|---|
| **Region** | Which AWS data center. Use **US East (N. Virginia) = `us-east-1`** for everything here. The region picker is in the top-right of the console. If something "disappeared", you are almost always in the wrong region. |
| **Stack** | A group of AWS resources created together by CloudFormation. Ours is called `CirohStack`. |
| **CDK** | The tool that turns the Python in `infra/` into a stack and deploys it. |
| **ARN** | A long unique ID for an AWS resource, like `arn:aws:rds:us-east-1:123456789012:cluster:...`. |
| **IAM** | AWS's permissions system. |

---

## Part 1 - Sign in and check your account (console)

### 1.1 Sign in

A "subaccount" is almost always a **member account** in your university's AWS
Organization. You were probably given one of these:

- **An "AWS access portal" link** (looks like `https://d-xxxxxxxxxx.awsapps.com/start`
  or `https://<name>.awsapps.com/start`). This is IAM Identity Center (SSO).
  Open it, sign in, click your account, then click the role name (e.g.
  `AdministratorAccess`) to open the console. **Bookmark this link. You'll
  also need it in Part 2.**
- **An account ID + IAM username + password.** Go to
  <https://console.aws.amazon.com/>, choose **IAM user**, enter the account
  ID, then your username and password.
- **A root email + password** for a brand-new account. Sign in as root once,
  then create a normal user for daily work (search the console for
  **IAM Identity Center** and follow "Enable", or ask your AWS admin).
  Don't do day-to-day work as root.

### 1.2 Set the region

Top-right of the console, next to your account name: click the region and
choose **US East (N. Virginia) us-east-1**.

### 1.3 Note your account ID

Click your account name (top-right). Copy the 12-digit **Account ID**
somewhere handy.

### 1.4 Check you have enough permissions

The deploy creates IAM roles, a VPC, a database, Lambda, CloudFront, WAF,
etc. You need broad permissions, usually a role/permission set called
**AdministratorAccess**. (`PowerUserAccess` is **not** enough, because it can't
create IAM roles.)

Quick check: type **IAM** in the top search bar, open it, click **Roles**. If
you see a list (not a red "not authorized" box), you're probably fine. If
you're unsure, ask whoever gave you the account:

> "Does my role in this account have AdministratorAccess (enough to run
> `cdk bootstrap` and create IAM roles), and are Amazon Bedrock, AWS
> Marketplace, and AWS Budgets allowed by our organization's SCPs?"

That one question prevents the most common subaccount problems.

### 1.5 (Recommended) A safety-net budget

Search **Budgets** → **Create budget** → **Use a template** → **Monthly cost
budget** → amount `50` → your email → **Create budget**. You'll get emails if
spend heads past $50 in a month. (If the Billing pages say "access denied",
your organization manages billing centrally; skip this. The stack also
creates Bedrock-specific budget alarms in Part 4.)

---

## Part 2 - Install the tools (your Windows laptop)

You already have **Node.js** and **Python** (3.12 or 3.13 both work). You do
**not** need Docker.

### 2.1 Install the AWS CLI

Download and run the installer: <https://awscli.amazonaws.com/AWSCLIV2.msi>.
Then **close and reopen** PowerShell and check:

```bash
aws --version
```

### 2.2 Install the AWS CDK CLI

```bash
npm install -g aws-cdk
```

```bash
cdk --version
```

### 2.3 Connect the CLI to your AWS account

**If you sign in through an access portal (SSO)**, the most common case:

```bash
aws configure sso
```

Answer the prompts:

| Prompt | What to type |
|---|---|
| SSO session name | `ciroh` |
| SSO start URL | your access portal link from Part 1.1 |
| SSO region | the region your portal is in (usually `us-east-1`; it's shown in the portal URL's settings, or ask your admin) |
| SSO registration scopes | press Enter |

A browser window opens. Click **Allow**. Back in the terminal, pick your
account and the AdministratorAccess role, then:

| Prompt | What to type |
|---|---|
| Default client Region | `us-east-1` |
| CLI default output format | `json` |
| Profile name | **`default`** (so you never need `--profile`) |

SSO logins expire after a few hours. When a command says the token has
expired, run `aws sso login` and continue.

**If you sign in with an IAM username/password instead:** in the console go
to **IAM → Users → (your user) → Security credentials → Create access key**,
choose "Command Line Interface", and copy the two keys. Then run
`aws configure` and paste them, with region `us-east-1` and format `json`.
Treat these keys like a password and never commit them.

Verify it works (this must print your 12-digit account ID):

```bash
aws sts get-caller-identity
```

### 2.4 Python environment for this repo

From the repo root, in PowerShell:

```bash
python -m venv .venv
```

```bash
.venv\Scripts\Activate.ps1
```

If PowerShell refuses with "running scripts is disabled on this system",
that's a Windows setting for your user account. You can allow locally
created scripts with `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`,
or use **Command Prompt** and run `.venv\Scripts\activate.bat` instead.

Your prompt now starts with `(.venv)`. **Activate it again in every new
terminal** before running anything below. Install everything (infra + backend):

```bash
pip install -r infra/requirements.txt -r backend/requirements.txt
```

---

## Part 3 - Turn on the Bedrock models (console, ~5 minutes)

Bedrock serves two models for this app: **Claude Haiku 4.5** (writes the
answers) and **Titan Text Embeddings V2** (turns text into vectors).
Anthropic models need a one-time setup per account, and it has to be done
by **you** (a person), not by the deployed app.

1. Console search bar → **Amazon Bedrock**. Confirm the region is
   **N. Virginia** (top-right).
2. Left menu → **Model catalog**. Search **Claude Haiku 4.5** and open it.
3. If you see a prompt to **submit use case details**, fill it in. Company:
   *University of Alabama / CIROH*. Use case: *"Retrieval-augmented Q&A
   chatbot over CIROH hydrology documentation for researchers."* Submit, and
   wait ~5 minutes.
4. Click **Open in playground** (or left menu → **Playgrounds → Chat**,
   select Anthropic → Claude Haiku 4.5), type `hello`, and send. Getting a
   reply creates the one-time AWS Marketplace subscription for your account.
5. Titan Text Embeddings V2 (an Amazon model) needs no setup.

Now confirm from the terminal:

```bash
python scripts/check_bedrock_access.py
```

You want both lines to say `[OK]`. If not, the script prints what to do. If
it mentions an **SCP / organization / Marketplace**, your university blocks
Bedrock or Marketplace in this account. Send the printed error to your AWS
admin; you can't fix that yourself.

---

## Part 4 - Deploy the infrastructure (terminal, ~20 minutes)

### 4.1 Settings

Open [`infra/cdk.json`](../infra/cdk.json) and set your email for cost and
error alerts:

```json
"budget_alert_email": "you@crimson.ua.edu",
```

Put it here rather than passing `-c` on the command line, so every later
deploy keeps it. The other values are sensible defaults:
`aurora_min_acu: 0` (database sleeps when idle), `budget_monthly_usd: 60`.

### 4.2 Bootstrap (once per account/region)

CDK needs a small "toolkit" stack in your account to upload files. From the
`infra` folder:

```bash
cd infra
```

```bash
cdk bootstrap
```

It ends with `Environment aws://<account>/us-east-1 bootstrapped`.

*Console:* **CloudFormation** → Stacks now shows **CDKToolkit**.

### 4.3 Deploy

```bash
cdk deploy CirohStack
```

1. First it builds the Lambda package with pip. You'll see "Bundling Lambda
   package with local pip (no Docker needed)".
2. It shows the IAM/security changes and asks `Do you wish to deploy these
   changes (y/n)?`. Type `y`.
3. It then takes **~15-25 minutes**: the Aurora database and the CloudFront
   distribution are the slow parts. Don't close the terminal.

*Console, while you wait:* **CloudFormation → Stacks → CirohStack → Events**
shows each resource being created live. If anything fails, the **first**
red `CREATE_FAILED` event (scroll to the oldest one) is the real reason.
The rest are just the rollback.

When it finishes you get **Outputs**:

```
CirohStack.FrontendUrl        = https://dxxxxxxxxxxxxx.cloudfront.net
CirohStack.ApiDomainName      = xxxxxxxxxx.execute-api.us-east-1.amazonaws.com
CirohStack.AuroraClusterArn   = arn:aws:rds:us-east-1:...:cluster:ciroh-docuhub-aurora
CirohStack.AuroraSecretArn    = arn:aws:secretsmanager:us-east-1:...
CirohStack.GuardrailId        = ...
```

You don't need to copy these. The scripts below read them from the stack
automatically. (They're always visible under **CloudFormation → CirohStack →
Outputs**.)

**Check your email:** AWS SNS sends a "Subscription Confirmation". Click
**Confirm subscription**, or you won't get alerts.

*Console - look at what you built (all in us-east-1):*

| Service (search bar) | What you'll see |
|---|---|
| **Aurora and RDS → Databases** | `ciroh-docuhub-aurora`, Serverless v2, empty for now |
| **Lambda → Functions** | `ciroh-docuhub-ask` |
| **API Gateway** | `CIROH-DocuHub-api` (HTTP API) |
| **CloudFront** | a distribution; its domain is your `FrontendUrl` |
| **S3** | a bucket named `cirohstack-frontend...` (empty until Part 6) |
| **Amazon Bedrock → Guardrails** | `CIROH-DocuHub-scope-guardrail` |
| **WAF & Shield → Web ACLs** (choose *Global (CloudFront)*) | `CIROH-DocuHub-waf` |

---

## Part 5 - Load the knowledge base into Aurora (~15-40 minutes)

The existing corpus lives in the Azure Postgres database with **OpenAI**
embeddings, which can't be reused on AWS (Titan's vectors aren't
comparable). The migration script reads every artifact and chunk from Azure,
re-embeds it with Titan via Bedrock, and loads it into Aurora. It costs well
under $1 in Bedrock charges.

### 5.1 Azure credentials

You need read access to the Azure `ciroh` database (the same `.env` the app
uses for local development; see the root README). In the **repo root**, make
sure `.env` contains:

```env
POSTGRES_HOST=c-ciroh-cluster.6cijvkzzmrtw2p.postgres.cosmos.azure.com
POSTGRES_DB=ciroh
POSTGRES_SCHEMA=CIROH_AIBot
POSTGRES_USER=raguser
POSTGRES_PASSWORD=<ask a teammate>
```

If the Azure server only allows listed IP addresses, your laptop's IP needs
to be on that list. Your teammate who manages the Azure DB can add it.

### 5.2 Run the migration, step by step

From the **repo root** (with `.venv` active):

```bash
cd backend/database
```

1. **Create the tables in Aurora.** The first statement waits ~15s while the
   sleeping database wakes up.

   ```bash
   python migrate_to_bedrock.py --apply-schema
   ```

2. **Check the source connection** (reads Azure, writes nothing). You should
   see several hundred artifacts and several thousand chunks:

   ```bash
   python migrate_to_bedrock.py --dry-run
   ```

3. **Smoke test** with 20 artifacts:

   ```bash
   python migrate_to_bedrock.py --limit 20
   ```

4. **Full run.** Rows already loaded are skipped, so this picks up where the
   smoke test left off:

   ```bash
   python migrate_to_bedrock.py
   ```

   It prints progress per batch of 200. **If it gets interrupted** (SSO
   expired, Wi-Fi dropped), run `aws sso login` if needed and run the same
   command again. It resumes from where it stopped.

5. **Validate retrieval:**

   ```bash
   python migrate_to_bedrock.py --validate --sample-question "What is NextGen In A Box?" --sample-question "How do I request AWS resources from CIROH?"
   ```

   Expect `Orphan chunks: 0` and `Artifacts with NULL embedding: 0`, and for
   each question 3 relevant titles with **distances around 0.3-0.6**
   (0 = identical meaning, higher = less related). Those distances are also
   how you tune the off-topic gate later (GUARDRAILS_AND_COST.md).

*Console - see the data yourself:* **Aurora and RDS → Query editor** →
database `ciroh-docuhub-aurora` → **Connect with a Secrets Manager ARN** →
paste the `AuroraSecretArn` output → database name `ciroh` → Connect. Run:

```sql
SELECT COUNT(*) FROM tblartifacts;
SELECT title, url FROM tblartifacts LIMIT 10;
```

---

## Part 6 - Publish the website (~5-10 minutes)

From the **repo root**:

```bash
python scripts/deploy_frontend.py
```

This runs `npm install` and `npm run build` in `frontend/`, then `cdk deploy`
again, which now also uploads `frontend/dist/` to S3 and clears the
CloudFront cache.

**Important:** from now on `frontend/dist/` exists, and every `cdk deploy`
publishes whatever is in it. Always redeploy the frontend with this script,
so it's rebuilt for production first.

---

## Part 7 - Test it

### 7.1 Automated end-to-end test

```bash
python scripts/smoke_test.py
```

It goes through CloudFront exactly like a browser: wakes the database, asks
two real questions (expect `[OK]`, answers, sources, and each under ~15s),
and one off-topic question (expect it to be refused).

### 7.2 In the browser

Open the `FrontendUrl` (e.g. `https://dxxxxxxxxxxxxx.cloudfront.net`). Click
the chat icon, then ask:

- *What is NextGen In A Box?*
- *How do I get started with the CIROH JupyterHub?*
- *Write me an essay about the French revolution.* (should be declined)

**First question after ~5+ minutes of no use:** Aurora pauses when idle to
save money and takes ~15s to wake. Opening the chat panel starts waking it,
so by the time you've typed a question it's usually ready. If you ask
instantly and get an error, ask again. See Troubleshooting if that happens
a lot.

### 7.3 Watch it working (console)

- **CloudWatch → Log groups → `/ciroh-docuhub/ciroh-docuhub-ask`** → newest log
  stream. Each question is a `TELEMETRY {...}` line with route, token usage
  and estimated cost. Errors show up here too.
- **Lambda → ciroh-docuhub-ask → Monitor** for invocations, duration, errors.
- **Amazon Bedrock → Guardrails → CIROH-DocuHub-scope-guardrail** to see
  what's being blocked.
- **Billing and Cost Management → Cost Explorer** (next day): filter
  *Service = Amazon Bedrock* to see real per-question costs.

---

## Part 8 - Tuning and day-to-day changes

| I want to... | Do this |
|---|---|
| Change backend code (`backend/rag`, `backend/aws`, `backend/database`) | `cd infra` then `cdk deploy CirohStack` |
| Change the frontend | `python scripts/deploy_frontend.py` |
| Stop real questions being rejected as off-topic (or let fewer off-topic ones through) | Change `retrieval_similarity_threshold` in `infra/cdk.json` (higher = more permissive), then `cdk deploy CirohStack`. See GUARDRAILS_AND_COST.md. |
| Avoid the ~15s wake-up delay entirely | Set `aurora_min_acu` to `0.5` in `infra/cdk.json` and redeploy. Costs about $43/month more. |
| Re-load the corpus after the Azure DB changes | Re-run Part 5 steps 4-5 (new rows are added, existing ones kept) |
| Use a custom domain (e.g. `chat.ciroh.org`) | Needs Route 53/ACM, not set up yet; see AWS_ARCHITECTURE.md |

For quick experiments you can also edit environment variables directly in
**Lambda → ciroh-docuhub-ask → Configuration → Environment variables**.
The next `cdk deploy` resets them to the values in the code, so make
permanent changes in `infra/`.

---

## Part 9 - Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Unable to resolve AWS account` / `Token has expired` / `ExpiredToken` | SSO login expired: `aws sso login`, then retry. |
| `cdk bootstrap` or `cdk deploy` fails with `AccessDenied` / "not authorized to perform iam:CreateRole" | Your role lacks permissions. Ask your admin for AdministratorAccess on the subaccount (Part 1.4). |
| Deploy fails on `AWS::Budgets::Budget` (explicit deny / SCP) | Your org blocks Budgets for member accounts. Set `"enable_budgets": false` in `infra/cdk.json` and deploy again. |
| Deploy fails; stack is `ROLLBACK_COMPLETE` | Read the **first** `CREATE_FAILED` in CloudFormation → Events. Fix it, then delete the failed stack (CloudFormation → CirohStack → Delete) and `cdk deploy` again. |
| `check_bedrock_access.py` fails on Claude | Redo Part 3 (use-case form + one playground message). If it mentions SCP/Marketplace, your admin must allow it. |
| Migration: `could not connect to server` / timeout on Azure | Wrong `.env` values or your IP isn't allowed on the Azure DB firewall. |
| Migration: `DatabaseResumingException` | Aurora is waking up. The script retries automatically; if it still fails, re-run the same command. |
| Chat shows an error on the **first** question after a while | Aurora was asleep. Ask again. If it's frequent, set `aurora_min_acu: 0.5`. |
| HTTP **504** on `/ask` | The request took over ~29s (API Gateway's hard limit). Usually a cold database plus a long "both" route. Retry; check the Lambda logs for which step is slow. |
| HTTP **403** on `/ask` | AWS WAF blocked it: rate limit (500 questions / 5 min per IP) or a managed rule. **WAF & Shield → Web ACLs (Global) → CIROH-DocuHub-waf → Sampled requests** shows which rule. |
| Every answer is "This assistant only answers questions about CIROH DocuHub content" | Either the corpus isn't loaded (run `--validate`) or the threshold is too strict: look at the distances `--validate` prints and raise `retrieval_similarity_threshold`. |
| Lambda log shows `AccessDeniedException` calling Bedrock | Model setup (Part 3) not done in us-east-1. |
| Browser still shows the old frontend | CloudFront cache: wait a minute and hard-refresh (Ctrl+F5). `deploy_frontend.py` already invalidates the cache. |

---

## Part 10 - Tearing it down

To delete everything this guide created (the database and all its data
included, since `env_name` is `dev`):

```bash
cd infra
```

```bash
cdk destroy CirohStack
```

This takes ~10-20 minutes (CloudFront is slow to delete). The small
`CDKToolkit` stack from `cdk bootstrap` can stay. It costs essentially
nothing and is reused by future deploys.

For a real long-lived deployment, set `"env_name": "prod"` in
`infra/cdk.json` before deploying: then deleting the stack keeps a final
database snapshot and the website bucket instead of destroying them.

---

## Cutover from Azure (after testing)

Following the migration plan's Section 10:

1. Run the app on AWS for a while; compare answers to the Azure version on
   known questions.
2. Point people/links at the CloudFront URL (or a custom domain).
3. Keep the Azure Postgres read-only for a short overlap window.
4. Then decommission the Azure PostgreSQL server and retire the OpenAI key.
   The AWS deployment never uses it (`LLM_PROVIDER=bedrock` is set in
   `infra/stacks/backend_stack.py`).

Local development is unchanged throughout: without `LLM_PROVIDER`/`DB_BACKEND`
in `.env`, `backend/rag` still uses OpenAI + Azure exactly as before.

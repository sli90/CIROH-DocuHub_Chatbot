# Deploying to AWS

A step-by-step walkthrough for standing up the serverless AWS stack
described in [AWS_ARCHITECTURE.md](./AWS_ARCHITECTURE.md), from a clean AWS
account to a working `/ask` endpoint serving real answers from a re-embedded
corpus. See [GUARDRAILS_AND_COST.md](./GUARDRAILS_AND_COST.md) for the
guardrail/threshold tuning that should happen alongside this, and
[AWS_ARCHITECTURE.md#known-limitations](./AWS_ARCHITECTURE.md#known-limitations-read-before-cutover)
for things to validate before treating this as production-ready.

## Prerequisites

- An AWS account with billing configured, and permissions to create IAM
  roles, VPCs, Aurora clusters, Lambda, API Gateway, CloudFront, WAF, ECS,
  Bedrock, Budgets, and Secrets Manager resources.
- **AWS CLI v2**, configured (`aws configure` or AWS SSO) with a profile
  that has the above permissions.
- **Node.js 18+** and the **AWS CDK CLI**: `npm install -g aws-cdk`.
- **Docker Desktop**, running. CDK uses it to bundle the Lambda package
  (`infra/stacks/backend_stack.py`, installs `backend/requirements-lambda.txt`
  into a Lambda-compatible image) and to build the ingestion task image
  (`backend/ingestion.Dockerfile`). Without Docker running, `cdk deploy`
  fails at the asset-bundling step with `spawnSync docker ENOENT`.
- **Python 3.12** for `infra/` (a separate virtualenv from `backend/`'s -
  CDK's own Python dependencies don't need to mix with the app's).
- **Node 18+** and `npm` for building the frontend (already required
  locally, see root README).

## 0. Enable Bedrock model access (do this first)

Bedrock model access is a manual, per-model, per-region opt-in - easy to
forget until the first Lambda invocation fails with an access-denied error.
In the target region's Bedrock console: **Model access** -> request access
to:

- Anthropic Claude Haiku 4.5
- Amazon Titan Text Embeddings V2

Approval for Anthropic models can take a few minutes to a few hours the
first time an account requests them. Do this before anything else in this
guide so it isn't the last-minute surprise the source plan (Section 11)
warns about.

## 1. Bootstrap and configure CDK

```bash
cd infra
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

cdk bootstrap aws://<ACCOUNT_ID>/<REGION>
```

Review `infra/cdk.json`'s `context` block - in particular
`aurora_min_acu`/`aurora_max_acu` (cost ceiling, Section 7.1) and
`budget_monthly_usd`. Override any of them per-deploy with `-c key=value`
rather than editing the file, e.g.:

```bash
cdk deploy CirohStack -c budget_alert_email=you@example.com -c budget_monthly_usd=60
```

## 2. First deploy (backend + empty frontend bucket)

```bash
cdk deploy CirohStack
```

This provisions everything in one CloudFormation stack: the VPC, the empty
Aurora Serverless v2 cluster, the Bedrock Guardrail, the Lambda + API
Gateway + WAF, an (empty, since `frontend/dist` doesn't exist yet) S3 bucket
+ CloudFront distribution, the Fargate ingestion task definition, and the
Budgets/CloudWatch alarms. Note the outputs:

```
CirohStack.ApiDomainName = xxxxxxxxxx.execute-api.us-east-1.amazonaws.com
CirohStack.FrontendDomainName = xxxxxxxxxx.cloudfront.net
CirohStack.AuroraClusterArn = arn:aws:rds:...
CirohStack.AuroraSecretArn = arn:aws:secretsmanager:...
CirohStack.GuardrailId = ...
```

### Two-phase deploy note (CORS)

`ALLOWED_ORIGINS` on the Lambda (for local/direct-API CORS - production
traffic through CloudFront is same-origin and doesn't need it, see
[AWS_ARCHITECTURE.md](./AWS_ARCHITECTURE.md#how-a-request-flows-production))
defaults to `http://localhost:5173` until you pass
`-c allowed_origins=https://<FrontendDomainName>`. If you need CORS to work
against the deployed API from somewhere other than the CloudFront domain
(e.g. testing the API directly), redeploy once with that context value
after step 2's `FrontendDomainName` output is known:

```bash
cdk deploy CirohStack -c allowed_origins="http://localhost:5173,https://xxxxxxxxxx.cloudfront.net"
```

## 3. Re-embed and load the corpus

This is the critical-path step (source plan, Executive Summary: "the single
largest migration task is not code, it is re-embedding the existing
document corpus"). OpenAI's and Titan's embedding spaces are not
comparable, so there's no way to reuse existing vectors.

**3a. Apply the schema** to the new (empty) Aurora cluster:

```bash
aws rds-data execute-statement \
  --resource-arn "$(cdk output CirohStack.AuroraClusterArn 2>/dev/null || echo <AuroraClusterArn>)" \
  --secret-arn "<AuroraSecretArn>" \
  --database ciroh \
  --sql "$(cat ../backend/database/schema_aws.sql)"
```

(`cdk output` isn't a real subcommand - copy the ARNs from step 2's output
or `aws cloudformation describe-stacks --stack-name CirohStack`.)

**3b. Run the migration script** from `backend/` with the destination env
vars set (see `env-template.txt`'s AWS section):

```bash
cd ../backend
python -m venv .venv && .venv\Scripts\activate  # if not already using one with requirements.txt installed
pip install -r requirements.txt

set AURORA_CLUSTER_ARN=<AuroraClusterArn>
set AURORA_SECRET_ARN=<AuroraSecretArn>
set AURORA_DATABASE=ciroh
set AURORA_REGION=<REGION>

cd database
python migrate_to_bedrock.py --dry-run          # sanity check row counts first
python migrate_to_bedrock.py --limit 50          # smoke test
python migrate_to_bedrock.py                     # full run (use --resume if it's interrupted)
python migrate_to_bedrock.py --validate --sample-question "What is NextGen In A Box?"
```

Spot-check the `--validate` output's retrieved titles/distances against
questions you know the answer to before treating the corpus as ready
(source plan, Section 11: "must be fully re-embedded and validated for
retrieval quality... before cutover, since it cannot be partially
migrated"). Two integration details worth spiking early rather than
discovering at cutover (already handled in `rds_data_client.py`, but worth
knowing about): pgvector's `vector` type isn't a native Data API type (it's
passed as a stringified array and cast via `::vector`), and the Data API
caps individual result rows at 64 KB - check your largest `chunk_text` row
if migration errors mention row size.

## 4. Build and deploy the frontend

```bash
cd ../../frontend
set VITE_API_BASE_URL=
npm install
npm run build
```

`VITE_API_BASE_URL=""` (empty) is deliberate: in production the frontend is
served from the same CloudFront distribution as the API
(`/ask`/`/telemetry` cache behaviors), so requests should go to same-origin
relative paths - see
[AWS_ARCHITECTURE.md, "why /ask stays /ask"](./AWS_ARCHITECTURE.md#why-ask-stays-ask-not-apiask).

Redeploy the CDK stack so `BucketDeployment` picks up `frontend/dist/`
(it's conditional on that directory existing, `infra/app.py`):

```bash
cd ../infra
cdk deploy CirohStack
```

Visit `https://<FrontendDomainName>` and ask it something.

## 5. Cutover

Following the source plan's step order (Section 10):

1. Validate end-to-end against the new stack (steps 2-4 above), including
   the [known limitations](./AWS_ARCHITECTURE.md#known-limitations-read-before-cutover)
   - especially real-traffic latency against the 29s API Gateway cap.
2. Point any external DNS/bookmarks at the CloudFront domain (or set up a
   custom domain via Route 53 + ACM first, which also makes step 2's
   `allowed_origins` deterministic before any deploy).
3. Keep the Azure Postgres instance available read-only for a short overlap
   window rather than decommissioning it immediately.
4. Once confident, decommission the Azure PostgreSQL Flexible Server and
   remove the OpenAI API key from wherever it's stored - the AWS side
   never needs it (`LLM_PROVIDER=bedrock` is set unconditionally in
   `infra/stacks/backend_stack.py`'s Lambda environment).

## Updating the deployed app later

- **Backend/infra code change**: `cd infra && cdk deploy CirohStack`.
- **Frontend-only change**: `cd frontend && npm run build && cd ../infra && cdk deploy CirohStack`
  (redeploying picks up the new `dist/` via `BucketDeployment` and
  invalidates CloudFront automatically).
- **Corpus content change** (once ingestion automation exists - see
  [AWS_ARCHITECTURE.md](./AWS_ARCHITECTURE.md#known-limitations-read-before-cutover)):
  `aws ecs run-task` against the `Ingestion` cluster/task definition, or
  enable the EventBridge schedule in `infra/stacks/ingestion_stack.py`.

## Rollback

Every resource in this stack (Aurora, Lambda, S3, CloudFront, ...) lives in
one CloudFormation stack, `CirohStack`. `cdk deploy` on a previous commit
rolls the whole stack back to that state in one operation; there's no
manual per-resource rollback needed. The Azure/OpenAI path keeps working
unchanged throughout (nothing here modifies the existing codebase's default
behavior - `LLM_PROVIDER`/`DB_BACKEND` both default to the pre-migration
values), so the safest rollback during the overlap window is simply
pointing traffic back at the existing Azure-backed deployment.

## Cost of tearing this down for a test deploy

`infra/cdk.json`'s `env_name` context defaults to `"dev"`, which sets
`RemovalPolicy.DESTROY` on the Aurora cluster and frontend bucket
(`infra/app.py`) - `cdk destroy CirohStack` removes everything cleanly for
a throwaway test account. Set `-c env_name=prod` for a real deployment,
which switches those to `SNAPSHOT`/`RETAIN` so a stack deletion can't
silently take the database or frontend assets with it.

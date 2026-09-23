# AWS Architecture Reference

This documents the AWS target architecture actually implemented in this repo
(`backend/aws/`, `backend/database/rds_data_client.py`, `infra/`), adapted from
the source planning document
(`CIROH_DocuHub_Chatbot_AWS_Migration_PlanV2.pdf`, August 2026). The plan was
written against an earlier repository layout (`ai_logic.py`, `tblurls`/
`tblcontent`, `backend/CIROH-scraper`); this branch (`v2-dev`) uses different
names (`backend/rag/ask.py`, `tblartifacts`/`tblchunks`, no scraper yet), so
every reference below points at what actually exists in this branch, not the
plan's illustrative names. The underlying strategy - serverless-first, one
AWS invoice via Bedrock, cost/scope guardrails - is unchanged.

## Component mapping

| Today (this repo, local dev) | AWS replacement | Where in this repo |
|---|---|---|
| `uvicorn main:app` (always-on) | Lambda (`rag.lambda_handler.handler`) behind API Gateway HTTP API | [`backend/rag/lambda_handler.py`](../backend/rag/lambda_handler.py), [`infra/stacks/backend_stack.py`](../infra/stacks/backend_stack.py) |
| Azure PostgreSQL + pgvector, psycopg2 | Aurora Serverless v2 + pgvector, RDS Data API | [`backend/database/rds_data_client.py`](../backend/database/rds_data_client.py), [`infra/stacks/database_stack.py`](../infra/stacks/database_stack.py) |
| OpenAI `gpt-5.5` (Responses API) | Amazon Bedrock, Claude Haiku 4.5 (Converse API) | [`backend/aws/bedrock_client.py`](../backend/aws/bedrock_client.py) |
| OpenAI `text-embedding-3-large` (1792-dim) | Amazon Bedrock, Titan Text Embeddings V2 (1024-dim) | [`backend/aws/bedrock_client.py`](../backend/aws/bedrock_client.py) |
| Notebook-driven scraper/populate scripts | On-demand/scheduled ECS Fargate task | [`backend/ingestion.Dockerfile`](../backend/ingestion.Dockerfile), [`infra/stacks/ingestion_stack.py`](../infra/stacks/ingestion_stack.py) |
| React/Vite SPA, served by `npm run dev` | S3 + CloudFront | [`infra/stacks/frontend_stack.py`](../infra/stacks/frontend_stack.py) |
| (none today) | AWS WAF (on CloudFront) + API Gateway throttling | [`infra/stacks/frontend_stack.py`](../infra/stacks/frontend_stack.py), [`infra/stacks/backend_stack.py`](../infra/stacks/backend_stack.py) |
| (none today) | AWS Budgets + CloudWatch alarms | [`infra/stacks/observability_stack.py`](../infra/stacks/observability_stack.py) |
| (none today) | Amazon Bedrock Guardrails (denied topics, prompt-attack) | [`infra/stacks/guardrail_stack.py`](../infra/stacks/guardrail_stack.py) |

## How a request flows (production)

1. Browser loads the SPA from CloudFront (S3 origin, cached).
2. The SPA POSTs `{ "text": "..." }` to `/ask` (same route as local dev -
   unchanged, see "why /ask stays /ask" below). CloudFront matches the
   `/ask` and `/telemetry` cache behaviors and forwards to the API Gateway
   origin instead of S3 - **same-origin**, so browser CORS doesn't apply to
   normal production traffic.
3. AWS WAF, attached to the CloudFront distribution
   (`infra/stacks/frontend_stack.py`), evaluates the request: a rate-based
   rule on `/ask` (requests per 5-minute window per viewer IP) and the AWS
   Managed Common Rule Set. WAF sits on CloudFront rather than on API
   Gateway because WAF cannot be attached to HTTP APIs, and at CloudFront it
   sees the real viewer IP.
4. API Gateway (HTTP API) applies its own throttle (steady-state + burst) and
   invokes the Lambda function synchronously.
5. Lambda (`rag/lambda_handler.py`, Mangum-wrapped FastAPI app) runs
   `ask_ai()` -> `answer_question()` (`backend/rag/ask.py`), unchanged in
   shape from local dev.
6. `answer_question()`:
   a. If `BEDROCK_GUARDRAIL_ID` is set, pre-screens the raw question via
      `ApplyGuardrail` (denied-topics match rejects here, before any other
      cost is incurred).
   b. Embeds the question via Titan Text Embeddings V2
      (`bedrock_client.get_embedding`).
   c. Runs the existing hybrid-route classifier and top-down/bottom-up
      retrieval against Aurora via the RDS Data API
      (`rds_data_client.RdsDataApiManager`) - same SQL, same recursive-CTE
      breadcrumb queries as local dev.
   d. **Retrieval-gate guardrail**: if nothing retrieved beats
      `RETRIEVAL_SIMILARITY_THRESHOLD`, returns a canned refusal here,
      skipping the chat-completion call entirely.
   e. Calls Claude Haiku 4.5 via Bedrock Converse
      (`bedrock_client.converse_text`), with the domain/scope system prompt
      sent through Converse's dedicated `system` parameter (not blended into
      the user message) and the retrieved context wrapped in
      `<context>...</context>` tags (indirect prompt-injection defense).
7. Lambda returns `{ answer, sources, links, route, usage, ... }` through API
   Gateway and CloudFront back to the browser.
8. CloudWatch (Lambda logs, API Gateway access logs, Bedrock invocation
   metrics) feeds the alarms and budgets in
   `infra/stacks/observability_stack.py`.

### Why `/ask` stays `/ask` (not `/api/ask`)

The source plan's Section 4 describes the SPA calling `/api/ask` with
CloudFront routing that prefix to the API origin. This repo's frontend
already calls `/ask` and `/telemetry` (`frontend/src/config/api.ts`,
`backend/rag/main.py`), so `infra/stacks/frontend_stack.py` configures
CloudFront cache behaviors for those exact paths instead of renaming
routes - zero frontend or backend route changes needed for the migration.

### Cold start note

If Aurora has scaled to 0 ACU (`aurora_min_acu=0`, the default), the first
Data API call after idle incurs a one-time resume of roughly 15 seconds.
Acceptable for a low-traffic internal tool; if unacceptable, set a small
non-zero `aurora_min_acu` (e.g. `0.5`) via CDK context, at a small fixed
monthly cost.

## Data layer: why Aurora, not a pure vector store

`backend/database/schema.sql` (and its AWS counterpart,
`backend/database/schema_aws.sql`) uses recursive CTEs
(`backend/rag/ask.py`'s `get_breadcrumb()`) and foreign-key joins between
`tblartifacts` and `tblchunks`. A pure vector store (Pinecone-style, or
AWS's own S3 Vectors - see "Appendix B" below) has no SQL joins or
recursion, so it isn't a drop-in replacement without rewriting that
hierarchy logic. Aurora Serverless v2 keeps the same PostgreSQL engine, the
same schema, and the same queries, while adding scale-to-zero and the Data
API.

`schema_aws.sql` differs from `schema.sql` in exactly one way:
`vector(1024)` instead of `vector(1792)`, because Titan Text Embeddings V2's
recommended output dimension is 1024 (OpenAI's 1792-dim matryoshka-truncated
vectors and Titan's vectors are not comparable - see
[CORPUS re-embedding](./AWS_DEPLOYMENT.md#3-re-embed-and-load-the-corpus)).

## AI layer: model choices

| Model | Role | Notes |
|---|---|---|
| `us.anthropic.claude-haiku-4-5-20251001-v1:0` | Answer generation | Fast/cheap. The `us.` prefix is a cross-region inference profile, which Haiku 4.5 requires for on-demand use |
| `amazon.titan-embed-text-v2:0` | Embeddings (query + corpus) | 1024 dimensions (configurable via `BEDROCK_EMBED_DIMENSIONS`) |

Both are read from environment variables
(`BEDROCK_CHAT_MODEL_ID`/`BEDROCK_EMBED_MODEL_ID` in
`backend/aws/bedrock_client.py`), so repointing to a different Bedrock model
(e.g. Claude Sonnet 4.5 for harder synthesis questions) is a config change,
not a code change.

## Known limitations (read before cutover)

- **API Gateway's 29-second integration timeout is fixed and cannot be
  raised** (true for both REST and HTTP APIs, all AWS accounts). The
  existing frontend already assumes slow answers are possible
  (`frontend/src/config/api.ts` sets an 180s client-side timeout because
  "Hybrid RAG + gpt-5.x often exceeds 30s" with OpenAI). Claude Haiku 4.5 is
  chosen specifically for being fast, and should comfortably answer within
  29s, but **validate this against real hybrid-route latency before
  cutover** - if a `both` route (top-down + bottom-up + answer) is ever
  slower than 29s, API Gateway returns a 504 regardless of what Lambda is
  doing. If that happens, the documented fix is a Lambda Function URL behind
  CloudFront + WAF instead of API Gateway (Function URLs allow the full
  15-minute Lambda timeout) - a bigger change than swapping one CDK
  construct, so it isn't implemented speculatively here.
- **`RETRIEVAL_SIMILARITY_THRESHOLD` (default `0.7`) is a starting guess**,
  not a tuned value - see [GUARDRAILS_AND_COST.md](./GUARDRAILS_AND_COST.md).
- **Anthropic models need a one-time, per-account setup by a person**
  (use-case form + one playground invocation, which creates the AWS
  Marketplace subscription) before the Lambda role can call them - see
  [AWS_DEPLOYMENT.md, Part 3](./AWS_DEPLOYMENT.md#part-3---turn-on-the-bedrock-models-console-5-minutes).
- **Aurora scale-to-zero:** the first query after ~5 idle minutes gets
  `DatabaseResumingException` while the cluster wakes (~15s).
  `rds_data_client.py` retries through it, and `/telemetry`'s `chat_open`
  event starts the resume when a user opens the chat panel, so it usually
  overlaps with typing the first question.
- **Contextual grounding (Section 9.2) is not enabled yet.** The Guardrail
  evaluates only the user's question (sent as a `guardContent` block), since
  retrieved docs legitimately contain code that would trip the
  "unrelated code" topic. Grounding needs the context/question tagged as
  `grounding_source`/`query` and a threshold tuned on real answers.
- **The day-to-day ingestion pipeline is still notebook-driven** in this
  branch (`PopulateDB.ipynb`, `GitHub_CodeRepos.ipynb`,
  `HydroShare_Datasets.ipynb` - see README, "In Progress / Planned").
  `infra/stacks/ingestion_stack.py` defines a Fargate task runner (opt-in
  with `-c enable_ingestion=true`, since building its image needs Docker)
  and `backend/database/migrate_to_bedrock.py` runs fine from a laptop
  today, but recurring automated ingestion needs those notebooks converted
  to scripts first; the EventBridge schedule is created disabled for this
  reason.

## Appendix: S3 Vectors as a later-phase optimization

Amazon S3 Vectors is a fully serverless vector store with no idle floor at
all (storage + query cost only, no Aurora ACU-hour minimum). It doesn't
support SQL joins or recursive queries, so adopting it means rewriting the
breadcrumb/URL-trail logic to be pre-computed and denormalized as vector
metadata at ingestion time rather than queried relationally at request
time. Worth revisiting once this Aurora-based design has run long enough to
know real traffic patterns and real cost (Section 8's methodology, not just
its numbers, is what to re-run) - not implemented in this migration.

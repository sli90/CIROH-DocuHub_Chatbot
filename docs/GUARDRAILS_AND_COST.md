# Guardrails and Cost Controls

What stops a public `/ask` endpoint from becoming a free homework helper or
a runaway AWS bill, where each control lives, and what to tune before
trusting the defaults.

## Defense-in-depth summary

| Layer | Mechanism | Where | What it stops |
|---|---|---|---|
| 1. Bedrock Guardrails pre-screen | `ApplyGuardrail` on the raw question, before embedding | `answer_question()`, `backend/rag/ask.py` | Obviously off-topic requests, rejected before the embedding call or any DB round-trip |
| 2. Retrieval-gate | Reject if nothing retrieved beats `RETRIEVAL_SIMILARITY_THRESHOLD` | `answer_question()`, `backend/rag/ask.py` | Off-topic questions that don't score close to any corpus page, before the chat-completion call |
| 3. System-role scope lock | Domain/refusal rules sent via Bedrock Converse's dedicated `system` parameter, not blended into the user message | `SYSTEM_MSG`, `get_rag_answer()`, `backend/rag/ask.py` | "Ignore your instructions" style direct injection |
| 4. Bedrock Guardrails (denied topics + prompt-attack) | Managed policy checked on every Converse call | `infra/stacks/guardrail_stack.py`, wired via `BEDROCK_GUARDRAIL_ID` | Homework/essay/code requests that survive layer 2 (e.g. share vocabulary with hydrology docs) |
| 5. Context delimiting | Retrieved content wrapped in `<context>...</context>` | `get_rag_answer()`, `backend/rag/ask.py` | Gives the model a structural signal for where untrusted retrieved text starts/ends |
| 6. Contextual grounding check | Bedrock Guardrails' RAG-specific grounding/relevance filters | `infra/stacks/guardrail_stack.py` | Indirect injection via scraped content: output that drifts from what was actually retrieved |
| 7. Output token cap | `maxTokens` on every Converse call (`MAX_ANSWER_TOKENS`, default 500) | `bedrock_client.converse_text()` | Caps how much "work" even a successful jailbreak can extract per request |
| 8. Input length validation | `Field(max_length=2000)` on the question | `backend/rag/main.py` | Oversized payloads padding token cost or attempting length-based injection |
| 9. WAF rate limit + managed rules | Rate-based rule (per-IP, 5-min window) + AWS Managed Common Rule Set | `infra/stacks/backend_stack.py` | Volume abuse, independent of what any single request asks for |
| 10. API Gateway throttling | Steady-state/burst request limits | `infra/stacks/backend_stack.py` | Same, a second layer |
| 11. AWS Budgets | 50/80/100% alarms, scoped to Bedrock specifically and to the project cost tag overall | `infra/stacks/observability_stack.py` | A runaway bill actually reaching the invoice before anyone notices |

Layers 1-8 are about **scope and content** (would answer even without a cost
concern); layers 9-11 are about **volume/cost**. Both matter independently.

## What to tune before trusting the defaults

Every default here is a starting guess (mirrors the source plan's own
framing, Section 11: "starting guess; plan to tune... in the first few
weeks"), not a validated value:

- **`RETRIEVAL_SIMILARITY_THRESHOLD` (default `0.7`)** - pgvector cosine
  distance, 0 = identical, 2 = opposite. Run a batch of known-on-topic and
  known-off-topic questions through `backend/rag/ask.py`'s
  `answer_question()` (or hit `/ask` directly) and look at the `route`
  field: on-topic questions that come back `"rejected"` mean the threshold
  is too strict; off-topic questions that get a real answer mean it's too
  loose. Tune per corpus, not per deploy - a larger, denser corpus tends to
  score real matches slightly further from center too.
- **WAF `waf_rate_limit_per_5min` (default `1000`) and API Gateway
  `rate_limit`/`burst_limit` (default `50`/`100`)**
  (`infra/stacks/backend_stack.py`) - set from nothing (no current
  production traffic to measure), tune against real usage.
- **`MAX_ANSWER_TOKENS` (default `500`)** - the source plan's Section 6.3
  worked example (1,500 input + 300 output tokens ≈ $0.003/question on
  Haiku 4.5) assumes answers stay well under this cap; raise it only if
  answers are being cut off, since it directly caps worst-case per-request
  cost.
- **Bedrock Guardrails' denied-topics examples**
  (`infra/stacks/guardrail_stack.py`) - the three topics defined there
  (general homework help, unrelated code generation, open-ended off-topic)
  are illustrative starting examples, not exhaustive. Add more `examples`
  entries as real misuse patterns show up in CloudWatch logs (layer 4's
  denied-topic violations are logged - alert on a spike from one
  IP/session, source plan Section 9.1).
- **`budget_monthly_usd` (CDK context, default `60`)** - matches the source
  plan's "Low" traffic tier estimate (Section 8.2, ~500 questions/month,
  $18-28/month total). Re-derive using Section 8.2's methodology (not just
  its dollar figures) once real question volume is known - the Bedrock
  sub-budget is set to 60% of this as a starting split between "LLM/
  embedding spend" and "everything else."

## Cost model quick reference

From the source plan, Section 8.2 (verify current rates in the Bedrock/RDS/
CloudFront pricing pages before finalizing a real budget):

| Traffic tier | ~Questions/month | Approx. total |
|---|---|---|
| Low | 500 | $18-28 |
| Moderate | 5,000 | $35-65 |
| High | 50,000 | $165-310 |

Bedrock is billed per-token (Haiku 4.5: $1/$5 per M input/output tokens;
Titan Embed V2: $0.02/M tokens) under the "Amazon Bedrock" line in AWS Cost
Explorer, itemized by model ID - no separate OpenAI account/balance to keep
funded, no dashboard outside AWS to check. Cost-allocation tags
(`Project=<project_name>`, `Environment=<env_name>`, applied at the stack
level in `infra/app.py`) let Cost Explorer and Budgets roll up this
project's spend specifically, separate from anything else in the same AWS
account.

## What this does *not* protect against

`backend/rag/main.py`'s Lambda only ever returns model output as text for
the browser to display - the model never executes code, calls tools, or
takes any action on the user's behalf. A successful prompt injection here is
limited to "the model says something it shouldn't," not "the model does
something it shouldn't." If a future version adds agentic tool use (the
model calling external APIs or modifying data), this whole document needs
revisiting - that's the point where prompt injection stops being a content
problem and becomes a system-compromise problem.

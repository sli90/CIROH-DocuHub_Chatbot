"""Amazon Bedrock Guardrails: denied-topics, prompt-attack, and contextual
grounding policy (AWS Migration Plan, Section 9.1 and 9.2).

Backs the second and third layers of the off-topic/misuse defense-in-depth
table in Section 9.1 (the retrieval-gate similarity threshold is the first
layer, implemented in backend/rag/ask.py, not here): a denied-topics policy
for homework/essay and unrelated code-generation requests, the built-in prompt-attack
filter for direct injection (Section 9.2).

The guardrail evaluates only the user's question (backend/aws/bedrock_client.py
sends it as a guardContent block), not the retrieved documentation, which
legitimately contains code and commands. Section 9.2's contextual grounding
check is not enabled yet: it needs the context and question tagged as
grounding_source/query and a threshold tuned on real answers, or it
rejects correct but synthesized answers. Indirect injection is handled by
the system prompt and <context> delimiting in backend/rag/ask.py.

Optional by design: backend_stack.py accepts guardrail_id=None and simply
skips passing guardrailConfig to Bedrock calls, so a deployment can ship
without this stack and add it later without touching application code.
"""

from __future__ import annotations

import hashlib

from aws_cdk import aws_bedrock as bedrock
from constructs import Construct


class GuardrailStack(Construct):
    def __init__(self, scope: Construct, construct_id: str, *, project_name: str) -> None:
        super().__init__(scope, construct_id)

        self.guardrail = bedrock.CfnGuardrail(
            self,
            "Guardrail",
            name=f"{project_name}-scope-guardrail",
            # CloudFormation caps this at 200 characters.
            description=(
                "CIROH DocuHub assistant: refuse homework help, essay writing, unrelated "
                "code generation and off-topic requests; block prompt-injection attempts."
            ),
            blocked_input_messaging=(
                "This assistant only answers questions about CIROH DocuHub content."
            ),
            blocked_outputs_messaging=(
                "This assistant only answers questions about CIROH DocuHub content."
            ),
            topic_policy_config=bedrock.CfnGuardrail.TopicPolicyConfigProperty(
                topics_config=[
                    bedrock.CfnGuardrail.TopicConfigProperty(
                        name="GeneralHomeworkHelp",
                        definition=(
                            "Requests to solve academic exercises, homework problems, or "
                            "assignments unrelated to CIROH documentation or hydrology tooling."
                        ),
                        type="DENY",
                        examples=[
                            "Solve this integral for me.",
                            "Write my essay about climate change.",
                            "Do my homework assignment.",
                        ],
                    ),
                    bedrock.CfnGuardrail.TopicConfigProperty(
                        name="UnrelatedCodeGeneration",
                        definition=(
                            "Requests to generate general-purpose code that has nothing to "
                            "do with CIROH hydrology tooling, datasets, or documentation."
                        ),
                        type="DENY",
                        examples=[
                            "Write a Python script that reverses a linked list.",
                            "Build me a to-do list app in React.",
                        ],
                    ),
                ]
            ),
            content_policy_config=bedrock.CfnGuardrail.ContentPolicyConfigProperty(
                filters_config=[
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        type="PROMPT_ATTACK",
                        input_strength="HIGH",
                        output_strength="NONE",
                    ),
                ]
            ),
        )

        # A version is a snapshot, only re-published when this resource is
        # replaced. Its properties are create-only, so putting a fingerprint
        # of the policy in the description publishes a new version (and
        # repoints the Lambda at it) whenever the topics/filters change.
        policy_fingerprint = hashlib.sha256(
            repr((self.guardrail.topic_policy_config, self.guardrail.content_policy_config)).encode()
        ).hexdigest()[:12]
        version = bedrock.CfnGuardrailVersion(
            self,
            "GuardrailVersion",
            guardrail_identifier=self.guardrail.attr_guardrail_id,
            description=f"Published version for production use, policy {policy_fingerprint}.",
        )

        self.guardrail_id = self.guardrail.attr_guardrail_id
        self.guardrail_version = version.attr_version

"""AWS Budgets alarms + CloudWatch alarms (AWS Migration Plan, Section 8.4).

Two budgets, both alarming at 50/80/100% of the same monthly ceiling
(Section 6.2 and 8.4): one scoped to Amazon Bedrock specifically (LLM/
embedding spend is the most volatile line item), one scoped to the
project's cost-allocation tag overall (everything else - Aurora, Lambda,
CloudFront, WAF, ...). Plus CloudWatch alarms on the two signals that most
directly indicate cost-abuse or malfunction: Lambda error rate and API
Gateway 4xx rate.

Cost allocation tags (Project=<project_name>) are applied at the App level
in app.py, not here - tags need to land on every resource in every stack,
and Aspects/tags.of(app) at the top is the simplest way to guarantee that.
"""

from __future__ import annotations

from typing import Optional

from aws_cdk import Duration
from aws_cdk import aws_budgets as budgets
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_cloudwatch_actions as cw_actions
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as subscriptions
from constructs import Construct


class ObservabilityStack(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_name: str,
        function: _lambda.IFunction,
        http_api_id: str,
        monthly_budget_usd: float,
        alert_email: Optional[str] = None,
        enable_budgets: bool = True,
    ) -> None:
        super().__init__(scope, construct_id)

        self.alert_topic = sns.Topic(self, "AlertTopic", topic_name=f"{project_name}-alerts")
        if alert_email:
            self.alert_topic.add_subscription(subscriptions.EmailSubscription(alert_email))
        # AWS Budgets needs an explicit resource policy grant to publish to
        # an SNS topic - it is not implied by adding it as a subscriber.
        self.alert_topic.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AllowAwsBudgetsPublish",
                principals=[iam.ServicePrincipal("budgets.amazonaws.com")],
                actions=["sns:Publish"],
                resources=[self.alert_topic.topic_arn],
            )
        )

        if enable_budgets:
            self._budgets(project_name, monthly_budget_usd)

        cloudwatch.Alarm(
            self,
            "LambdaErrorAlarm",
            alarm_name=f"{project_name}-ask-lambda-errors",
            metric=function.metric_errors(period=Duration.minutes(5)),
            threshold=5,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
        ).add_alarm_action(cw_actions.SnsAction(self.alert_topic))

        api_4xx = cloudwatch.Metric(
            namespace="AWS/ApiGateway",
            metric_name="4xx",
            dimensions_map={"ApiId": http_api_id},
            period=Duration.minutes(5),
            statistic="Sum",
        )
        cloudwatch.Alarm(
            self,
            "Api4xxAlarm",
            alarm_name=f"{project_name}-api-4xx-spike",
            metric=api_4xx,
            threshold=50,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
        ).add_alarm_action(cw_actions.SnsAction(self.alert_topic))

    def _budgets(self, project_name: str, monthly_budget_usd: float) -> None:
        # The tag-scoped budget only sees spend once the "Project" cost
        # allocation tag is activated in Billing (from the organization's
        # management account, for a member/sub account). The Bedrock one
        # works immediately.
        self._budget(
            "ProjectBudget",
            f"{project_name}-monthly-total",
            monthly_budget_usd,
            cost_filters={"TagKeyValue": [f"user:Project${project_name}"]},
        )
        self._budget(
            "BedrockBudget",
            f"{project_name}-monthly-bedrock",
            monthly_budget_usd * 0.6,  # Bedrock is the most volatile line item; tighter cap
            cost_filters={"Service": ["Amazon Bedrock"]},
        )

    def _budget(self, construct_id: str, name: str, amount: float, cost_filters: dict) -> None:
        notifications = []
        for threshold in (50, 80, 100):
            notifications.append(
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        notification_type="ACTUAL",
                        comparison_operator="GREATER_THAN",
                        threshold=threshold,
                        threshold_type="PERCENTAGE",
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            subscription_type="SNS",
                            address=self.alert_topic.topic_arn,
                        )
                    ],
                )
            )
        budgets.CfnBudget(
            self,
            construct_id,
            budget=budgets.CfnBudget.BudgetDataProperty(
                budget_name=name,
                budget_type="COST",
                time_unit="MONTHLY",
                budget_limit=budgets.CfnBudget.SpendProperty(amount=amount, unit="USD"),
                cost_filters=cost_filters,
            ),
            notifications_with_subscribers=notifications,
        )

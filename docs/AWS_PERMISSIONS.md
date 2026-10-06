# AWS permissions for deploying the CIROH DocuHub chatbot

Everything needed to deploy and test with the CloudShell workflow
([AWS_DEPLOYMENT_CLOUDSHELL.md](./AWS_DEPLOYMENT_CLOUDSHELL.md)), in
region **us-east-1**. There are two ways for an admin to grant it.

## Option 1 - simplest

Give the deployer's role these AWS managed policies on the subaccount:

- `AdministratorAccess`, which already includes everything below,
  CloudShell included.

If the deployer **already has AdministratorAccess and CloudShell still
fails**, the block comes from the organization (a service control policy)
and must be fixed there. See "Organization-level requirements" below.

## Option 2 - least privilege

Two customer-managed policies, in [`docs/iam/`](./iam/). Replace
`ACCOUNT_ID` with the 12-digit account ID before creating them.

**A. [`ciroh-deployer-policy.json`](./iam/ciroh-deployer-policy.json)**:
attach to the deployer's role. It grants:

| What for | Permissions |
|---|---|
| Opening CloudShell (fixes "Unable to create the environment") | `cloudshell:*` |
| Running `cdk bootstrap` (one-time toolkit stack) | CloudFormation on `CDKToolkit`, IAM on `cdk-*` roles, S3/ECR/SSM on `cdk-*` resources |
| Running `cdk deploy` / `cdk destroy` | `sts:AssumeRole` on the `cdk-*` roles that bootstrap created, CloudFormation on `CirohStack` |
| Using Claude Haiku 4.5 + Titan embeddings, the guardrail | `bedrock:InvokeModel`, `bedrock:ApplyGuardrail`, Bedrock read, one-time model enablement (`bedrock:PutUseCaseForModelAccess`, `bedrock:CreateFoundationModelAgreement`) |
| One-time Anthropic model subscription | `aws-marketplace:Subscribe`, `Unsubscribe`, `ViewSubscriptions` |
| Loading the corpus into Aurora | `rds-data:*Statement` on the `ciroh-docuhub-aurora` cluster, `secretsmanager:GetSecretValue` on `CIROH-DocuHub/*` |
| RDS Query Editor in the console | `dbqms:*`, `rds:Describe*`, `secretsmanager:ListSecrets` |

Also attach the AWS managed **`ReadOnlyAccess`** policy, so the deployer can
look at what was created: CloudFormation events, CloudWatch logs, Lambda,
CloudFront, Cost Explorer, Budgets.

**B. [`ciroh-cdk-execution-policy.json`](./iam/ciroh-cdk-execution-policy.json)**:
what CloudFormation itself uses to create the stack's resources:

- a VPC with subnets, internet gateway, route tables and security groups
  (no NAT gateway, no EC2 instances)
- Aurora (RDS)
- Lambda
- API Gateway
- CloudFront
- WAF
- S3
- SNS
- Budgets
- CloudWatch alarms and logs
- a Bedrock guardrail
- a Secrets Manager secret
- IAM roles named `CirohStack-*` for the stack's own functions

CDK's default bootstrap gives CloudFormation `AdministratorAccess`. To use
this narrower policy instead, the admin creates it as a customer-managed
policy named `CirohCdkExecutionPolicy`, then bootstraps with it, once:

```bash
cdk bootstrap aws://ACCOUNT_ID/us-east-1 --cloudformation-execution-policies arn:aws:iam::ACCOUNT_ID:policy/CirohCdkExecutionPolicy
```

The admin can run that from their own CloudShell, which saves the
deployer needing any bootstrap permissions at all. If a later
`cdk deploy` fails with "not authorized to perform X", add X to this
policy.

## Organization-level requirements (SCPs, set in the management account)

These can't be granted inside the subaccount. If any is blocked, no IAM
policy above will help:

| Needed | Why |
|---|---|
| **CloudShell** allowed | The deployment runs from CloudShell. CloudShell also needs AWS Systems Manager session messaging (`ssmmessages`) to open its terminal. |
| **Region us-east-1** allowed | The app is deployed there. CloudFront's WAF can only be created in us-east-1. |
| **Bedrock in us-east-1, us-east-2, us-west-2** | Claude Haiku 4.5 is called through the US cross-region inference profile, which routes to those three regions. |
| **Global services** allowed: IAM, CloudFront, WAF (CloudFront scope), Budgets, STS | Region-restriction SCPs usually exempt these. They must, for this deploy. |
| **AWS Marketplace** subscribe allowed | One-time Anthropic model enablement. |
| **AWS Budgets** allowed (optional) | If not, the deployer sets `"enable_budgets": false` in `infra/cdk.json`. |
| **Cost allocation tag `Project`** activated (optional) | Lets the project budget and Cost Explorer track this app's spend. Only the management account can activate it. |

## About "Unable to create the environment" in CloudShell

That message means CloudShell isn't allowed for your role **in the region
the console is showing**. Try these in order:

1. Click **System error** in the message to see the exact reason. An
   explicit deny in a service control policy points to the organization;
   "not authorized to perform cloudshell:CreateEnvironment" means your
   role's policies.
2. Click **Open a tab** → **us-east-2** (the button the error offers). If
   CloudShell opens there, **you can use it**. CloudShell's own region
   doesn't matter: `scripts/cloudshell_setup.sh` points everything at
   us-east-1 regardless.
3. If no region works, the admin must allow `cloudshell:*` (Option 1 or 2)
   and make sure no SCP denies CloudShell.

Don't use **Create a VPC environment**. It needs extra network
permissions, and it has no persistent home folder, so your files would
vanish after 20-30 idle minutes.

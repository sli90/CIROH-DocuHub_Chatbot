# CI/CD: automatic deploys from `aws-bedrock-migration`

Every push to the `aws-bedrock-migration` branch runs
[.github/workflows/deploy.yml](../.github/workflows/deploy.yml):

1. **Tests**: backend API tests (`pytest backend/tests`, with Bedrock and
   Aurora faked, so no AWS access needed), frontend type check and unit tests.
2. **Deploy** (only if the tests pass):
   - builds the website (`npm run build`) and the Lambda package,
   - signs in to AWS as the `CIROH-DocuHub-github-deploy` role (no stored keys),
   - posts `cdk diff CirohStack` to the run's summary page,
   - runs `cdk deploy CirohStack`,
   - runs `scripts/smoke_test.py` against the live site (refuses a question
     without an email, streams an answer, asks two questions, checks an
     off-topic question is declined).

Pushes that only change `docs/**` or `*.md` files skip the workflow. A run
can also be started by hand: GitHub → **Actions** → **Test and deploy** →
**Run workflow**. Only one deploy runs at a time; a newer push waits for the
running one.

A deploy takes about 8–12 minutes. Watch it under the repo's **Actions** tab;
the run summary shows the infrastructure diff and the site URL.

## How AWS access works (no access keys)

GitHub gives each workflow run a short-lived signed token (OIDC) that says
which repository and branch it is running for. `infra/stacks/cicd_stack.py`
(the `CirohCicdStack` stack) sets up:

- an IAM OIDC identity provider for `token.actions.githubusercontent.com`;
- the role `CIROH-DocuHub-github-deploy`, which trusts only tokens for
  `repo:sli90/CIROH-DocuHub_Chatbot:ref:refs/heads/aws-bedrock-migration`,
  and whose only permission is to assume the CDK bootstrap roles
  (`cdk-hnb659fds-{deploy,file-publishing,image-publishing,lookup}-role-*`),
  the same roles `cdk deploy` uses from CloudShell.

So pull requests, forks and other branches cannot deploy, and the workflow
only ever deploys `CirohStack`. It cannot change its own permissions, which
live in `CirohCicdStack` and are deployed only by a person.

## One-time setup

### 1. Create the deploy role (CloudShell, once)

```bash
cd ~/ciroh && source scripts/cloudshell_setup.sh
cd infra
cdk diff CirohCicdStack
cdk deploy CirohCicdStack
```

The output `CirohCicdStack.GitHubDeployRoleArn` is the role ARN for step 2.

If it fails because the provider already exists ("Provider with url
https://token.actions.githubusercontent.com already exists"), the account
already trusts GitHub, so reuse that provider:

```bash
aws iam list-open-id-connect-providers
cdk deploy CirohCicdStack -c github_oidc_provider_arn=arn:aws:iam::<account>:oidc-provider/token.actions.githubusercontent.com
```

### 2. Tell GitHub which role to use (repo owner/admin)

In GitHub: **Settings → Secrets and variables → Actions → Variables tab →
New repository variable**

- Name: `AWS_DEPLOY_ROLE_ARN`
- Value: the `GitHubDeployRoleArn` output, e.g.
  `arn:aws:iam::<account-id>:role/CIROH-DocuHub-github-deploy`

It is a *variable*, not a secret: the ARN alone grants nothing. It is kept
out of the code only so the AWS account ID is not published in this public
repository. Until it is set, pushes still run the tests, and the run shows
a "Deploy skipped" warning.

### 3. Push

Any push to `aws-bedrock-migration` now tests and deploys.

## Changing the setup

| Want to... | Do this |
|---|---|
| Deploy from a different branch | Change `github_branch` in `infra/cdk.json` and `branches:` in the workflow, then `cdk deploy CirohCicdStack` |
| Repo moved or renamed | Change `github_repo` in `infra/cdk.json`, then `cdk deploy CirohCicdStack` |
| Require a manual approval before deploying | Use a GitHub environment with required reviewers. This changes the token's subject to `repo:<repo>:environment:<name>`, so update the `sub` condition in `cicd_stack.py` to match and redeploy `CirohCicdStack`. |
| Pause automatic deploys | Delete the `AWS_DEPLOY_ROLE_ARN` variable (tests keep running), or disable the workflow under Actions |
| Remove CI access entirely | `cdk destroy CirohCicdStack` |

Deploying by hand from CloudShell (docs/AWS_DEPLOYMENT_CLOUDSHELL.md) still
works and is unaffected. Name the stack (`cdk deploy CirohStack`), since
the app now has two stacks.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `Not authorized to perform sts:AssumeRoleWithWebIdentity` | The token didn't match the role's trust: wrong branch, repo renamed, or a GitHub environment added (see table above). |
| `cdk deploy` fails with `AccessDenied` on `cdk-hnb659fds-...` | The account was bootstrapped with a different qualifier or region; check `aws iam list-roles \| grep cdk-` and update `CDK_QUALIFIER` in `cicd_stack.py`. |
| Smoke test fails with `route: unavailable` | The database was waking up; re-run the job. |
| Smoke test fails with the daily limit | `smoke-test@ciroh-docuhub.invalid` hit 100 questions in a day (about 25 deploys); it resets at midnight US Central. |

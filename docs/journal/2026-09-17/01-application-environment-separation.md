---
date: 2026-09-17
sequence: 01
commit: <fill in after committing>
---

# Fixed: Application shared across environments, resolved AppBundle, reverted premature shared config

## The bug: every environment's stack tried to create the same Application

`infra-resource-pipeline`'s `Deploy_test` stage failed:
`The Elastic Beanstalk application snack-recommender does not have an environment called
snack-recommender-test` — actually a misleading downstream symptom; the real CloudFormation
error underneath was `Resource of type 'AWS::ElasticBeanstalk::Application' ... already exists`.

Root cause: an EB **Application** is a single, account-wide container that many
**Environments** live under — but `WebAppHosting`/`InfraStack` created a brand new
`CfnApplication` inside *every* environment's stack (`SnackRecommenderInfra-dev`, `-test`,
`-stage`, `-prod`), each trying to `CreateApplication` with the same name. `dev`'s stack
happened to run first and succeeded; `test`'s stack then hit the collision.

## First attempt (rejected): a boolean flag

Initial fix added `create_application: bool` to `WebAppHosting`, set `True` only for `dev`.
Correctly identified as a smell: a construct needing an external flag to decide *whether* to do
part of its job means that part doesn't belong in the construct at all — not a real fix, just a
narrower version of the same problem.

## Real fix: split into two constructs, two stacks, no flag

- **`ElasticBeanstalkApplication`** (construct) — creates the Application. Nothing else.
- **`ApplicationStack`** — owns `ElasticBeanstalkApplication`. Deployed once, ever, not
  per-environment.
- **`ElasticBeanstalkEnvironment`** (renamed from `WebAppHosting`) — creates one Environment
  only. Never creates or references an Application resource in its own template — just
  `application_name` as a plain string, assuming it already exists in AWS.
- **`EnvironmentStack`** (renamed from `InfraStack`) — owns `WebAppInstanceRole` +
  `ElasticBeanstalkEnvironment` for one environment. Requires the Application to already exist.

`app.py` now always instantiates `ApplicationStack` once, plus one `EnvironmentStack` per
`-c env=` invocation. Renaming was deliberate too, not just the split: "WebAppHosting" and
"InfraStack" were vague leftovers from before this separation existed; new names say exactly
what each thing does.

## Real bug hit during the rename: `self.environment` collides with CDK's own `Stack.environment`

`EnvironmentStack.__init__` tried `self.environment = ElasticBeanstalkEnvironment(...)` —
`AttributeError: property 'environment' of 'EnvironmentStack' object has no setter`. CDK's
`Stack` base class already defines a read-only `environment` property (account/region as a
string) that this collided with directly. Fixed by renaming the attribute to `self.eb_environment`.
Worth remembering: check for inherited property names before picking an attribute name on any
CDK construct/stack subclass.

## Decided (again, this time for real): AppBundle removed entirely

`AppBundle`'s fate had been deferred twice already, pending the app pipeline being proven
working — it now is. `AppBundle` is no longer wired into `EnvironmentStack`, and the construct
file itself was deleted rather than kept as a standalone bootstrap tool. A freshly created
environment has no `version_label` and serves EB's default sample app until the app pipeline's
first real deploy to it — expected, not a regression, and given the app pipeline can reach a new
environment within about a minute of it existing, not a meaningful gap in practice.

## Reverted: the shared `ENVIRONMENT_NAMES` extraction

Questioned whether `infra/infra/config/environments.py` (extracted a few days ago in
anticipation of a second resource type needing the same environment list) was actually earning
its keep. It wasn't — `elastic_beanstalk/config/environment.py` remains the only consumer, so
"shared" was aspirational, not real; the extraction just added a file and a cross-module import
for one assertion. Folded `ENVIRONMENT_NAMES` back into `elastic_beanstalk/config/environment.py`
directly and deleted `infra/infra/config/`. Documented the reversal condition explicitly in a
comment: extract it back out the day a second real consumer (RDS, etc.) actually needs it, not
before.

## Cleanup and redeploy

- Deleted the stuck `SnackRecommenderInfra-test` stack (`REVIEW_IN_PROGRESS` — a changeset had
  been proposed but never executed, so nothing was actually created; safe to delete).
- Destroyed and recreated `dev` from scratch rather than attempting `cdk import` to adopt the
  existing Application into the new `ApplicationStack` — chosen deliberately as the simpler,
  lower-risk path given `dev` had already been rebuilt several times today without issue.
- `cdk deploy SnackRecommenderApplication` then `cdk deploy SnackRecommenderInfra-dev` — both
  succeeded cleanly, confirmed via `cdk diff` beforehand that `SnackRecommenderInfra-dev`'s
  template contains no `Application` resource at all.

## Updated the resource pipeline for multi-stack deploys

Since `app.py` now synthesizes two stacks, a bare `cdk deploy -c env=X` (no stack name) would
fail once more than one stack exists. Updated `CdkDeployProject` to take an explicit
`stack_names: list[str]`, and `ResourcePipelineStack` to pass the right ones per environment:
`dev` deploys `["SnackRecommenderApplication", "SnackRecommenderInfra-dev"]`; `test`/`stage`/`prod`
each deploy only their own `SnackRecommenderInfra-<env>`. `cdk deploy ResourcePipelineStack`
updated all four CodeBuild projects' buildspecs in place — no replacement, ~12 seconds.

## Confirmed: the pipeline runs against `main`, not local files

Before re-triggering `infra-resource-pipeline` to test the actual fix, realized this fix exists
only on the local working branch — the pipeline's Source stage checks out `main`, which still
has the old buggy code. Manual `cdk deploy` commands worked regardless of branch because they
ran against local files directly; the pipeline doesn't. Merge to `main` required before the
resource pipeline can actually exercise this fix.

## Next up (not yet started)

- Merge this branch to `main`, then trigger `infra-resource-pipeline` and confirm `Deploy_test`
  succeeds for real this time.
- Re-trigger the app pipeline afterward — `Deploy_test` there needs `snack-recommender-test` to
  exist first.
- RDS/Postgres, HTTPS, real tests replacing the Build stage's placeholder.
- Update `docs/elastic-beanstalk/deploy-flow.md` — it still describes the old single-stack,
  AppBundle-wired-in model.
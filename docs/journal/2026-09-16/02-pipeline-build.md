---
date: 2026-09-16
sequence: 02
commit: 776dcdf
---

# Built the pipeline (CodeBuild + CodePipeline, targeting EB via a registry)

## Decided: pipeline stays a separate CDK project, not a cross-stack reference

Considered using a CDK cross-stack reference to pass `WebAppHosting`'s application/environment
directly into a pipeline stack, to avoid duplicating their names. Concluded it was unnecessary:
`application_name`/`environment_name` are plain strings chosen at authoring time, not
CloudFormation-generated tokens — there's nothing for a cross-stack reference to resolve that
isn't already known when writing the code. A cross-stack reference would have also forced
`pipeline/`'s CDK code to live inside the same `cdk.App()` as `infra/`, contradicting the
original plan for `pipeline/` to be a genuinely separate, sibling top-level project. Resolved by
using a small shared config registry instead (see below) — no CFN-level dependency between the
two CDK projects, ever.

## Built the pipeline

Confirmed CodeDeploy is **not** used for Elastic Beanstalk — CodePipeline has a native
`ElasticBeanstalk` deploy action provider that calls EB's own APIs
(`CreateApplicationVersion`/`UpdateEnvironment`) directly. CodeDeploy is for raw
EC2/ECS/Lambda deployments outside of EB's own orchestration, and would be redundant here.

Structure, mirroring the `infra/` project's own scaffolding:
- `pipeline/` — its own CDK project (`cdk init app --language python`), own `.venv`,
  `app.py`, `cdk.json`.
- `DeployTarget` (`Protocol`) — the interface the pipeline depends on, not a specific service.
  Anticipates future non-EB targets (microservices, frontends, Kafka topics) without the
  pipeline itself needing to branch on resource type.
- `ElasticBeanstalkDeployTarget` — the one real implementation right now, wraps
  `CodePipelineActions.ElasticBeanstalkDeployAction`.
- `TargetRef` / `TARGETS` registry (`pipeline/pipeline/config/targets.py`) — plain config
  mapping `(app, env)` to `source_path` + `application_name` + `environment_name`. This is what
  replaced the cross-stack reference: one small file both projects can independently stay
  consistent with, not a CFN-level coupling.
- `PipelineStack` — Source (GitHub via CodeStarConnection) → Build (CodeBuild, currently a
  placeholder — `test-apps/snack-recommender` has no automated tests yet) → Deploy
  (`ElasticBeanstalkDeployTarget`).

Noted but deliberately not built yet: a real "customer submits an action, pipeline dispatches
to the right workflow" layer, and a `DeployTarget` implementation for anything other than EB.
Named as the intended direction, not built ahead of an actual second use case (YAGNI).

Also flagged and deferred: once the pipeline does a real deploy via the EB API directly, it
updates `VersionLabel` outside of CloudFormation's knowledge. `AppBundle` in `infra/` still
thinks it owns that property, so the next unrelated `cdk deploy` in `infra/` (e.g. resizing an
instance) could revert the pipeline's most recent deploy. Decided not to guess at removing
`AppBundle`'s `version_label` wiring without first confirming how CloudFormation's EB resource
provider actually behaves when that property is removed from the template — risk of resetting
the environment to the sample app is worse than the known, already-understood drift warning.
Revisit once the pipeline has proven itself end-to-end.

## Deploying the pipeline stack — real issues hit

- CodeBuild's actual job here isn't "build" in the compiled sense — EB already runs
  `pip install` itself on the instance during deploy. CodeBuild's real purpose is running tests
  *before* anything ships, so broken code never reaches EB. Since `snack-recommender` has no
  tests yet, the Build stage is currently a placeholder (`echo` + `pip install -r
  requirements-dev.txt`) — swap in `pytest` once real tests exist.
- `cdk synth`/`cdk deploy` in `pipeline/` initially failed twice with the same shape of error:
  `ImportError: cannot import name 'TARGETS'` and later `TypeError: Stack.__init__() got an
  unexpected keyword argument 'github_owner'`. Root cause both times: the given file contents
  hadn't actually been placed on disk yet — `cdk init` had generated placeholder files that were
  never overwritten. Not a code bug; a reminder to verify file contents before assuming a paste
  landed.
- `cdk deploy` succeeded once the real files were in place: created the `CodeStarConnection`
  (`PENDING`), the CodeBuild project (with CDK auto-generating scoped IAM roles per pipeline
  stage), and the `CodePipeline` itself. Flagged: the EB deploy action's auto-generated role
  gets `AdministratorAccess-AWSElasticBeanstalk` attached — CDK's own default for this action,
  broader than the narrow, resource-scoped IAM approach used elsewhere in this project. Worth
  revisiting once the pipeline works end-to-end, not blocking right now.
- GitHub connection authorization: `aws codestar-connections list-connections` confirmed the
  connection existed and was `PENDING`. "Developer Tools" isn't a fixed console menu item
  anymore — found it instead by clicking directly into the connection from the CodePipeline
  console, which surfaced the "Update pending connection" option and the GitHub OAuth popup.
  Confirmed `AVAILABLE` afterward.
- First manual pipeline trigger still failed at Source: `git push` failed with
  `Invalid username or token. Password authentication is not supported for Git operations` —
  GitHub dropped password auth for git operations years ago; needs a PAT or `gh auth login`
  instead. Root cause underneath that: the working branch
  (`feature/cf-template-elastic-beanstalk`) had never actually been pushed to GitHub at all —
  the pipeline's Source stage had nothing to pull. Confirmed via
  `git log origin/<branch>..HEAD` before assuming a push would fix it.

## Next up (not yet started)

- Actually push the branch (auth fixed, push pending) and confirm the pipeline runs
  Source → Build → Deploy successfully end to end.
- Once confirmed working: decide `AppBundle`'s fate for real (bootstrap-only vs. removed) and
  test that change deliberately, not as part of another deploy.
- RDS/Postgres.
- HTTPS on the load balancer.
- The generalized multi-app/multi-resource-type direction — a real registry beyond one hardcoded
  `TargetRef`, and eventually the customer-action dispatcher layer, once a second real resource
  type exists to justify building it.

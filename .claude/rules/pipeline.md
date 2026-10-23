---
description: Verifying infra/pipeline fixes against real deploys, not just CI or a local cdk deploy.
paths: ["pipeline/**", "infra/**"]
---

# Pipeline & infra verification

Learned the hard way fixing #346: a real `cdk deploy` updates the live AWS resources (CodeBuild
project config, IAM roles, etc.) immediately, completely independent of git. It's easy to mistake
"I ran `cdk deploy` and the pipeline now behaves differently" for "the fix is actually in the
codebase" -- they're not the same thing. The pipeline's own source (what it builds and deploys)
only ever comes from `main` on GitHub. Before trusting a pipeline run as evidence a fix works,
confirm the fix is actually merged to `main`, not just that `cdk deploy` ran locally against the
current branch.

Relatedly: for any bug that is specifically a gap between CI and a real deploy (CI always runs
against a full checkout; a real deploy only ever gets a scoped artifact, a real IAM role, a real
EB instance lifecycle, etc.), CI passing is not evidence the bug is fixed -- by definition, CI
passing is exactly the thing that let the bug exist unnoticed in the first place. Verify this
category of bug against a real deploy (real pipeline execution, real logs, a real request against
the live instance) every time it's touched, not just once at the end.

See the `debug-pipeline` skill for the mechanics of triggering and debugging a real run.

## CloudFormation: omitting a property means "stop managing it," not "reset it"

Learned fixing #344: when a CloudFormation resource property is absent from the template,
CloudFormation doesn't touch that property at all on an update -- it's not treated as "no value,"
it's treated as "not CloudFormation's concern." This cuts both ways:

- A property that was **never** set and stays omitted won't get forced to some default on an
  unrelated update (why #344's feared `VersionLabel` revert didn't reproduce).
- A property that **was** set and then gets removed from the template does **not** get cleared on
  the real resource either -- the stale value just stays, silently, even though the deployed
  template correctly no longer lists it. Don't assume "I removed it from the code and redeployed"
  means "it's gone" -- verify against the real resource, and be ready to clear it directly via the
  AWS CLI (e.g. `aws elasticbeanstalk update-environment --description ""`) if it's a test
  artifact that needs real cleanup.

## Test more than one update path before concluding a repro failed

A single reproduction attempt that doesn't trigger the suspected behavior doesn't rule out the
behavior -- it only rules out that *one kind* of update. #344's first test (an `OptionSettings`-
only change) alone wouldn't have ruled out the revert being specific to that update type; only a
second, structurally different test (a top-level property change, not nested in `OptionSettings`)
made "not reproducible" a solid conclusion rather than a narrow one. When investigating a
suspected CloudFormation/infra behavior, pick at least two update paths that exercise genuinely
different parts of the resource before concluding either way.

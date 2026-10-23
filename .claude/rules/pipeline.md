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

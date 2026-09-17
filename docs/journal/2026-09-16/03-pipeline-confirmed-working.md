---
date: 2026-09-16
sequence: 03
commit: <fill in after committing>
---

# Pipeline confirmed working end to end

First real pipeline-driven deploy succeeded — code went from `git push` to a running change on
`snack-recommender-dev` with zero manual `cdk deploy` involved. This is the milestone the whole
`pipeline/` build was working toward.

## The bug that showed up on the first real Build attempt

Pipeline run failed at Build: `can't cd to test-apps/snack-recommender`, even though the exact
same `cd test-apps/snack-recommender` command had just succeeded in the Install phase moments
earlier in the same log.

Root cause: **CodeBuild's working directory persists across phases within one build** — it
doesn't reset between Install/Build/Post-build. So Install's `cd` left the shell sitting inside
`test-apps/snack-recommender`; Build's `cd test-apps/snack-recommender` then tried to go one
level *deeper* from there (`test-apps/snack-recommender/test-apps/snack-recommender`), which
doesn't exist. Not a missing-file or bad-push problem — confirmed the push itself was fine,
since the build got far enough to run real commands before failing.

Fixed by using `$CODEBUILD_SRC_DIR` (a variable CodeBuild always sets to the checkout root) as
the base of every `cd`, in every phase, rather than relying on relative paths that depend on
wherever the previous phase happened to leave the shell:
```
cd $CODEBUILD_SRC_DIR/test-apps/snack-recommender
```

## Deploying the fix

`cdk diff` in `pipeline/` showed the `BuildSpec` change plus several `KNOWN_AFTER_APPLY`
placeholders cascading into IAM policies and the pipeline's `ProjectName` reference — flagged by
CDK as `BuildProject may be replaced`, since changing a CodeBuild project's `BuildSpec` is
documented as a replacement-triggering property.

Actual result was better than predicted: `cdk deploy` produced `UPDATE_COMPLETE` on the same
logical resource (`BuildProject097C5DB7`) — an in-place update, not a full replacement. Worth
noting as a reminder that CDK's diff-time "may be replaced" is a conservative warning, not a
guarantee; the real CloudFormation behavior can turn out less disruptive. Deploy took under 12
seconds.

## Confirmed working

- Re-triggered the pipeline ("Release change") — Source, Build, and Deploy all succeeded,
  total run time 1m19s.
- Source correctly pulled the exact latest commit (`685eae30`, the docs commit).
- `aws elasticbeanstalk describe-environments` confirmed `Ready`/`Green` afterward.
- `/health` confirmed responding correctly in the browser.

This closes out the original goal from earlier in the day: prove the pipeline can deploy the
real app to EB without a human running `cdk deploy`.

## Next up (not yet started)

- Decide `AppBundle`'s fate for real now that the pipeline is proven — it still sets
  `version_label` on every `cdk deploy` in `infra/`, which will now conflict with what the
  pipeline sets directly via the EB API. This was deliberately deferred until the pipeline
  worked; it now does.
- RDS/Postgres.
- HTTPS on the load balancer.
- Swap the Build stage's placeholder commands for real `pytest` once tests exist.
- The multi-app/multi-resource-type direction (real `TARGETS` registry beyond one entry, the
  customer-action dispatcher layer) — once a second real resource type exists to justify it.

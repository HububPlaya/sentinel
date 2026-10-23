---
date: 2026-10-23
sequence: 01
commit: 1a466e4
---

# #344: omitting VersionLabel does not revert the EB environment's deployed version

Reproduced live against `snack-recommender-dev` before deciding a fix, per #344's own AC. Baseline:
the environment was running `code-pipeline-1792736648331-BuildOutput-86c698ae-7096-46a4-a616-d2f01c83db28`
(deployed by the real pipeline fixing #346), healthy.

Ran two separate real `cdk deploy` runs against `infra/`'s `SnackRecommenderInfra-dev` stack, each
an unrelated change that still touches the `AWS::ElasticBeanstalk::Environment` resource:

1. Adding a temporary EB environment variable (`OptionSettings`-only change).
2. Adding a temporary `Description` (a top-level resource property, not an `OptionSettings` entry
   -- a genuinely different part of the resource's update path, chosen specifically because the
   first test alone wouldn't rule out the revert being specific to `OptionSettings` updates).

`VersionLabel` stayed exactly `code-pipeline-...-86c698ae-...` across both, confirmed via
`aws elasticbeanstalk describe-environments` after each deploy. The feared revert -- a later,
unrelated `infra/` deploy clobbering the pipeline's most recently deployed version -- was **not
observed** under either realistic update. CloudFormation appears to simply never touch
`VersionLabel` when it's absent from the template, regardless of what else about the resource
changes in that same update.

Related finding, worth remembering even though it doesn't change #344's conclusion: removing the
temporary `Description` from the CDK code and redeploying did **not** clear it from the real
environment -- the stale text stayed on the live resource even though the deployed CloudFormation
template correctly no longer listed it. Had to clear it with a direct
`aws elasticbeanstalk update-environment --description ""` call. Same underlying mechanism as the
`VersionLabel` question (CloudFormation only pushes properties that are explicitly present in the
template; omitting a property doesn't mean "clear it," it means "stop managing it") -- but this is
a distinct risk (a stale value silently surviving a property's removal) from what #344 asked about
(an active value being reverted), and is not itself fixed here.

No code fix applied -- the specific mechanism #344 raised wasn't reproducible under realistic
conditions, so there's nothing concrete to change in `elastic_beanstalk_environment.py`. Closing
#344 with this real evidence rather than leaving it open on a theoretical risk that didn't hold up
when actually tested.

---
date: 2026-09-16
sequence: 01
commit: 6744e0a
---

# Fixed the hardcoded "webapp" name, extracted shared environment names

## Fixed the hardcoded "webapp" name

`app_name="webapp"` in `app.py` had a `# TODO: replace with your real frontend app name`
comment sitting on it since the very first version of `infra/app.py` — never actually resolved
once the real app (snack-recommender) existed. Caught while reviewing the project: `app_name`
was correctly threaded through to `AppBundle` and `WebAppHosting`, but **not** to
`WebAppInstanceRole`, which took no `app_name` parameter at all and instead hardcoded its own
independent default in `IamConfig` (`role_name: str = "webapp-eb-ec2-role"`, etc.) —
disconnected from whatever `app_name` was set to elsewhere. Renaming the app without this fix
would have left an EB Application named `snack-recommender` next to an IAM role still named
`webapp-eb-ec2-role-dev`.

Fixed by:
- Changing `IamConfig` to hold only suffixes (`role_name_suffix`, `instance_profile_name_suffix`),
  not full names.
- Giving `WebAppInstanceRole` a real `app_name` parameter, combined with the suffix at
  construction time.
- Threading `app_name` through from `InfraStack` the same way `AppBundle`/`WebAppHosting`
  already did.
- Renaming the app for real in `app.py`: `app_name="snack-recommender"`, stack renamed to
  `SnackRecommenderInfra-dev`.

Verified via `cdk synth` before deploying — confirmed `RoleName`, `InstanceProfileName`, and
`ApplicationName` were all consistently `snack-recommender-*` throughout the template, not a
mix of old and new. Required full resource replacement (role/profile/application names all
force CFN replacement), so did `cdk destroy` on the old `webapp-dev` stack first rather than
trust an in-place rename changeset. Fresh deploy succeeded; `/health` and `/snacks` confirmed
working under the new names.

## Extracted shared environment names

Discussed the goal of eventually supporting multiple apps/resource types (not just Elastic
Beanstalk) through one pipeline system. Before building that out, fixed a smaller but related
issue: `ENVIRONMENTS`/environment names (`dev`/`test`/`stage`/`prod`) were owned entirely by
`elastic_beanstalk/config/`, even though environment identity isn't actually EB-specific — a
future `rds/` submodule would need the exact same names.

Added `infra/infra/config/environments.py` — a shared `ENVIRONMENT_NAMES` list, sibling to
`elastic_beanstalk/`, not inside it. `elastic_beanstalk/config/environment.py` now imports it
and asserts `ENVIRONMENTS.keys()` matches it, so drift between the two fails loudly at
`cdk synth` rather than silently.

## Next up (not yet started)

- See journal entry 05 for the pipeline build that followed this same day.

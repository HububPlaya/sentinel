---
date: 2026-09-15
sequence: 03
commit: e68acb5
---

# Deployed the real app onto Elastic Beanstalk (AppBundle)

Replaced EB's default sample app with the actual snack-recommender Flask app — the mechanism
we'd deliberately deferred until now: an S3 asset, a `CfnApplicationVersion`, and wiring
`version_label` onto the environment.

## What went wrong, in order, and the real fixes

- **Invented a property that doesn't exist.** First pass passed `version_label` directly into
  `CfnApplicationVersion` — that resource has no such property. Confirmed against AWS's own
  CloudFormation reference: `AWS::ElasticBeanstalk::ApplicationVersion` only accepts
  `ApplicationName`, `SourceBundle`, `Description`. CloudFormation auto-generates the version
  label itself and exposes it via `Ref`. Fixed by passing
  `application_version.ref` as the environment's `version_label` instead of a string we made up.
  Side benefit: since changing `SourceBundle` forces CloudFormation to replace the resource, a
  code change automatically produces a new version — no manual label-bumping needed.
- **Parallel-creation race.** First real deploy failed:
  `No Application named 'webapp' found` on the `ApplicationVersion` resource.
  `application_name="webapp"` was set identically on both the `Application` and
  `ApplicationVersion` resources, but a matching *string* doesn't tell CloudFormation the two
  are related — only an actual `Ref`/`Fn::GetAtt` reference does. Without that, CFN created both
  in parallel and the version's creation hit the API before the application existed. Fixed with
  an explicit `application_version.add_resource_dependency(web_app_hosting.application)` in
  `infra_stack.py` — the Stack is the only place both constructs are visible, so that's where
  cross-construct dependencies belong.
- **Same latent bug found by inspection, not by failure.** `instance_profile_name` was being
  passed into `WebAppHosting` as a plain literal string
  (`self.instance_role.instance_profile.instance_profile_name`), not a token — meaning
  CloudFormation had no tracked dependency there either. It hadn't failed yet purely because IAM
  resources create fast and EB environments create slow, so timing happened to work out. Fixed
  by switching to `.ref` instead of `.instance_profile_name`, which resolves to a real `{Ref}`
  token CloudFormation does track automatically. General rule that came out of this: check
  whether a value threaded between resources is a token or a literal — only the former gets
  CloudFormation to enforce ordering for free.
- **Removed unnecessary `Optional`/`None` handling.** `app_source_path` on `InfraStack` was
  typed as optional with a `None` fallback and an `if self.app_bundle:` guard, but there is
  exactly one real caller (`app.py`) and it always passes a real path. Made it a required
  parameter and deleted the conditional — no speculative branch for a case nothing produces.
- **503 "back-end server is at capacity."** Misleading nginx wording for "can't reach the app
  process at all," not literal load. Root cause, found via
  `aws elasticbeanstalk retrieve-environment-info --info-type tail` →
  `/var/log/eb-engine.log`: `There is no proc command in proc file. Aborting the deployment.`
  The `Procfile` in the deployed bundle was **zero bytes** — content was never actually written
  to it locally before it got committed/deployed. Fixed by writing the real content
  (`web: gunicorn --bind :8000 --workers 3 wsgi:application`) via
  `[System.IO.File]::WriteAllText(...)` with an explicit no-BOM UTF-8 encoding (worth checking
  for on Windows generally — several editors/tools default to UTF-8-with-BOM, which can silently
  break line-prefix parsers like EB's Procfile reader even when the file *looks* fine).

## Clarified along the way

- The EB application's name (`"webapp"`) has no special meaning to AWS — it's just a string we
  picked. It was never the cause of the sample-app fallback or the deploy failure. The sample
  app shows whenever `version_label` is unset, regardless of the application's name.
- Whether `AppBundle` should keep owning app deploys once a real CI/CD pipeline exists is an
  open decision, not yet made: if a future pipeline updates `VersionLabel` directly via the EB
  API (bypassing CloudFormation), the next `cdk deploy` would see drift and could try to revert
  it. Current plan: keep `AppBundle` for bootstrapping a fresh environment; decide the pipeline's
  actual deploy mechanism when `pipeline/` is built, not before.

## Confirmed working

Full deploy succeeded end to end after the Procfile fix — environment healthy, `/health` and
`/snacks` reachable via the real Flask app instead of EB's sample page.

## Next up (not yet started)

- RDS/Postgres — `/snacks` currently 500s on the deployed environment since no tables exist
  there (SQLite defaults to an empty on-instance file; `init-db`/`seed-db` were only ever run
  locally).
- HTTPS on the load balancer.
- Decide and build the actual CI/CD pipeline, including resolving the AppBundle-vs-pipeline
  ownership question above.

---
date: 2026-10-22
sequence: 01
commit: 1f72e38
---

# platform_core was never actually installable on a real EB deploy (#346)

Reproduced live against `snack-recommender-dev` before writing any fix, per #346's own AC: ran
`aws codepipeline start-pipeline-execution --name snack-recommender-app-pipeline` and let it reach
`Deploy_dev` for real. It failed, and the real `eb-engine.log` confirmed the exact mechanism #346
predicted from reading the pipeline code:

```
ERROR: ../../platform_core is not a valid editable requirement. It should either be a path to a
local project or a VCS URL ...
Instance deployment failed to install application dependencies. The deployment failed.
```

Not silent, as the issue speculated it might be -- a hard, loud deploy failure (health went Red).
Still means no `snack-recommender` deploy had actually worked since `platform_core` became a
dependency; CI and local both always run against a full monorepo checkout, so `-e ../../platform_core`
resolves fine there and never surfaced this.

Considered three options from #346's own implementation notes (vendor-copy, wheel-in-bundle,
private package index). Chose a private AWS CodeArtifact repository: it removes the deploy-artifact-
scoping problem entirely instead of working around it, and is reusable for future onboarding apps
without a hand-rolled per-app vendoring step. A wheel-in-bundle approach would have needed the same
per-app bundling plumbing as vendoring; CodeArtifact doesn't.

Versioning is deliberately manual, not auto-generated: `platform_core`'s version lives in its own
`pyproject.toml`; the pipeline publishes whatever's currently declared there, idempotently (skips
if already published), and a consuming app pins to a matching version explicitly. Bumping the
version is the real "release" action.

Verified the same way as the reproduction -- a real pipeline execution, not just CI passing. Took
several more real-deploy iterations than expected, each one a genuine bug CI couldn't have caught:

- Two IAM resource-type mistakes (`GetRepositoryEndpoint`/`ReadFromRepository` are repository-level,
  not domain/package as first assumed; confirmed against the real API via
  `iam:SimulatePrincipalPolicy`, not just docs).
- A missing `codeartifact:ListPackageVersions` grant on the CodeBuild role, whose absence was
  masked by the publish step's own `2>/dev/null || echo 0` idempotency fallback -- every build
  thought nothing was published yet and tried to re-upload, hitting a real 409 once something
  actually existed.
- A shell-variable-scoping bug splitting the version lookup and the idempotency check across
  separate buildspec `commands` entries (fixed by chaining with `&&`).
- The EB prebuild hook reading `CODEARTIFACT_DOMAIN` etc. from env vars that don't exist yet at
  that phase of the EB deploy lifecycle -- fixed by hardcoding the (genuinely static,
  platform-wide) domain/repository name directly in the hook instead.
- The CodeArtifact IAM grant was only ever deployed to `SnackRecommenderInfra-dev`, not `-test`/
  `-stage`/`-prod` -- each environment's own EB instance role needed the same grant separately.

Final confirmation, 2026-10-23: `Deploy_dev` succeeded for real. `curl /health` on the live
`snack-recommender-dev` instance returned `{"status":"ok"}`, and the instance's own log shows
`platform_core`'s real structured OTel JSON for that exact request (`trace_id`, `app_id`, `team`,
`environment`, `severity`) -- not CI, not local, the actual deployed instance. `snack-recommender-test`
subsequently hit an unrelated, pre-existing bug (`ModuleNotFoundError: No module named 'psycopg'` in
its predeploy migration hook) with zero CodeArtifact-related errors, confirming this fix holds
there too; that separate bug is out of scope for #346.

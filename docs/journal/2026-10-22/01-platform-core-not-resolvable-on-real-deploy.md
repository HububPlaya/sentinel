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

Verification plan is the same as the reproduction: a real pipeline execution reaching `Deploy_dev`
and a real `/health` call, not just CI passing -- CI passing proves nothing new about this specific
bug class, since it's a CI-vs-real-deploy gap by definition. (This entry will be updated once that
real redeploy has actually run.)

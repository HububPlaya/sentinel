---
date: 2026-10-02
sequence: 03
commit: aeee684
---

# The pipeline's test stage never actually ran tests

`pipeline/pipeline/constructs/test_build_project.py`'s CodeBuild `build` phase was still the
original scaffolded placeholder: `echo 'No automated tests yet — placeholder build stage'`. Every
prior deploy through this pipeline passed that stage unconditionally, regardless of whether any
test existed or passed.

Replaced it with real test execution: installs and runs `platform_core`'s suite (its own
`--cov-fail-under=90` gate applies automatically), then the target app's own suite
(`snack-recommender`'s, for this target). `platform_core` has no dedicated pipeline target of its
own yet, so its tests run inside snack-recommender's build for now -- it'll re-run once per
environment stage (dev/test/stage/prod) until `platform_core` gets a real target, which is a
separate piece of work, not addressed here.

Coverage is enforced in CI now, but only visible in build logs -- nothing posts it onto the PR
itself yet. That would need CodeBuild pushing a GitHub status or comment, which doesn't exist.

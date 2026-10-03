# CLAUDE.md

Project-specific conventions for Claude Code sessions working in this repo. See also the global
`design-initiative`, `write-story`, `sprint-plan`, `tdd-commit-cycle`, and `scaffold-project`
skills for the project-agnostic planning/implementation methodology this repo follows.

## Branch naming

Branches use the **`feature/<short-kebab-case-description>`** form (e.g. `feature/telemetry-logging-schema`),
off `main`.

Note: `docs/pr-convention.md` currently documents a different, shorter `feat/` form and calls
`feature/` the legacy pattern. That doc predates a later explicit decision to use `feature/` going
forward. Follow `feature/` per this file until `docs/pr-convention.md` is updated to match --
don't silently pick one or the other, and flag the conflict if it comes up again.

## Commit messages

Otherwise follow `docs/pr-convention.md` as written: `type(scope): short summary` subject
(lowercase, imperative, no trailing period), blank line, then dash bullets stating what changed
and why. Match the style of recent real commits (`git log`) rather than a generic template.

## TDD workflow

When implementing a story, use strict test-driven development: one scenario at a time, confirm
the test fails for the right reason before writing any implementation, write the minimum code to
pass it, then commit. See the `tdd-commit-cycle` skill for the full method.

Commit granularity: scaffolding (new package layout, config, empty files) is its own commit,
separate from behavior. Each TDD cycle (one test + the minimal code that makes it pass) is one
commit, not batched with other cycles.

## Test coverage

New Python sub-projects (`platform_core`, and any future ones) enforce a minimum **90%** test
coverage via `pytest-cov`, wired into `pyproject.toml` so a plain `pytest` run fails below it --
not just a documented target. 90% was offered as a default suggestion (see `scaffold-project`
skill) and accepted as-is for `platform_core`; it was not independently re-derived for that
project, so revisit it if it ever causes real friction rather than treating it as fixed.

## CI

This repo's CI is **CodeBuild via CodePipeline**, defined in `pipeline/pipeline/constructs/`
(`test_build_project.py` for the test stage) -- not GitHub Actions. There's no `.github/workflows`
to look for. It's per-target (one test stage per app/environment combination in
`pipeline/config/targets.py`), not a single central pipeline. Before trusting that "tests run in
CI" for any app, go read the relevant construct directly -- the test stage was an unimplemented
`echo` placeholder for a while before anyone checked (see
`docs/journal/2026-10-02/03-ci-test-stage-was-a-placeholder.md`). `platform_core` has no dedicated
pipeline target of its own yet; its suite currently rides along inside `snack-recommender`'s build
stage and will re-run once per that app's environment stage until it gets a real target.

## Known pre-existing issues (not yours to silently "fix")

- `pipeline/tests/unit/test_pipeline_stack.py::test_sqs_queue_created` fails on `main`,
  independent of any change -- stale boilerplate missing required constructor args
  `PipelineStack` has always needed. Confirmed via `git stash` before attributing a failure here
  to your own change; don't assume you broke it.

## Flask gotchas

`TESTING=True` defaults `PROPAGATE_EXCEPTIONS` on, which bypasses registered
`app.errorhandler(Exception)` handlers so exceptions propagate for debugger convenience.
Production doesn't set `TESTING`, so it doesn't propagate there by default -- a test of
error-handling behavior needs `app.config["PROPAGATE_EXCEPTIONS"] = False` to actually exercise
the real path instead of Flask's test-mode shortcut. See
`docs/journal/2026-10-02/02-flask-testing-propagate-exceptions.md`.

## Journal entry granularity

The journal README says "one entry per commit." In practice, for a dense TDD session (a dozen-plus
small cycle commits for one story), write one entry per **distinct thing learned or decided**
instead -- not a mechanical one-per-commit count. Each entry still points at the one specific
commit where that thing landed.

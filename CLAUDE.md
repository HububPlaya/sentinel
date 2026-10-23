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

## Verifying infra/pipeline fixes

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

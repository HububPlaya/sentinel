# CLAUDE.md

Project-specific conventions for Claude Code sessions working in this repo. See also the global
`design-initiative`, `write-story`, `sprint-plan`, and `tdd-commit-cycle` skills for the
project-agnostic planning/implementation methodology this repo follows.

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

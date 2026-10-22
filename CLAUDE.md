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

## Two different kinds of "testing this platform," not one

This repo is a platform meant to onboard multiple customer app teams, but right now has only one
real app (`snack-recommender`), managed by the same person building the platform itself. That
makes it easy to conflate two genuinely different concerns -- keep them separate:

- **Platform-stack-internal testing**: validating changes to this repo's own `infra/`/`pipeline/`
  CDK code before they reach `main` (e.g. #344's version-label bug, `cdk synth`/`cdk diff` checks).
  This is the platform team's own CI concern, same as any codebase's.
- **Customer-capability testing**: validating the *features the platform offers to onboarded app
  teams* (ephemeral per-PR environments, scoped test credentials -- #260/#262/#263, under Epic
  #33 "Test Execution Infrastructure," explicitly "for app teams") -- these are product
  capabilities for customers, not this repo's own engineering practice.

Until a real second app team onboards, **a deliberately simulated second test app stands in for
a real customer tenant** to validate multi-tenant capabilities (concurrent-PR isolation, etc.)
rather than guessing at what a hypothetical future customer would need. When scoping a story,
say explicitly which of the two categories it belongs to -- don't let "we only have one app"
become a reason to quietly fold a customer-capability story into platform-internal work, or vice
versa.

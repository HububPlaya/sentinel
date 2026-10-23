# CLAUDE.md

Project-specific conventions for Claude Code sessions working in this repo. See also the global
`design-initiative`, `write-story`, `sprint-plan`, `tdd-commit-cycle`, and `scaffold-project`
skills for the project-agnostic planning/implementation methodology this repo follows, and
`.claude/rules/*.md` for topic-specific conventions (git/commit conventions, testing, pipeline
verification, Windows dev environment notes).

## Branch naming

Branches use the **`feature/<short-kebab-case-description>`** form (e.g. `feature/telemetry-logging-schema`),
off `main`.

Note: `docs/pr-convention.md` currently documents a different, shorter `feat/` form and calls
`feature/` the legacy pattern. That doc predates a later explicit decision to use `feature/` going
forward. Follow `feature/` per this file until `docs/pr-convention.md` is updated to match --
don't silently pick one or the other, and flag the conflict if it comes up again.

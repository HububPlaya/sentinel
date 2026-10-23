---
description: TDD workflow and test-coverage requirements for this repo.
paths: ["**/*"]
---

# Testing

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

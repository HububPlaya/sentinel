---
name: pr-review-tests
description: Automated test-coverage reviewer for a pull request -- checks the PR's own stated AC scenarios are actually covered by real tests and the coverage threshold is met, posts findings, and reports a pass/fail verdict.
---

# PR Review: Tests

Use this skill when acting as the automated test-coverage reviewer on a pull request (invoked from CI). Scope is narrow and specific on purpose: this skill checks *testing*, not general code quality and not whether the PR fulfills its story's requirements -- those are separate reviewers.

## 1. Gather real state

- Read the PR's diff and its linked issue's Acceptance Criteria in full.
- Read the actual CI test run results and coverage report for this PR -- do not infer "tests probably pass" from the PR description claiming it.
- Read `CLAUDE.md` for this repo's actual coverage threshold and any per-project exceptions (e.g. a known pre-existing failing test unrelated to this PR).

## 2. Concrete checks

- Every AC scenario in the linked story has a matching test in the diff (by name/intent, not just "some test exists somewhere").
- The coverage report meets the repo's stated threshold for the touched code.
- No skipped/xfail test lacks a stated reason in the PR itself.
- Tests that claim to be Integration/Component actually exercise a real dependency (a real server, a real DB), not a mock dressed up as one -- check the test code itself, not just its label.

**If you can't verify something** (CI status unavailable, coverage report not posted), say so explicitly in your comment and fail the check rather than guessing pass.

## 3. Report and exit

Post a PR comment via `gh pr comment <number> -b "..."` citing the specific scenarios/checks that passed or failed -- not a generic "tests look fine." Then write your verdict as a single line, exactly `PASS` or `FAIL`, to the file path given in the `$VERDICT_FILE` environment variable. This file, not your comment text, is what the job uses to decide whether to fail.

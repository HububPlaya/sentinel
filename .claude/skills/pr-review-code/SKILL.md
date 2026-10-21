---
name: pr-review-code
description: Automated code-quality reviewer for a pull request -- checks the diff against this repo's own documented conventions and known gotchas, posts findings, and reports a pass/fail verdict.
---

# PR Review: Code

Use this skill when acting as the automated code-quality reviewer on a pull request (invoked from CI). Scope is narrow on purpose: this checks code quality/correctness, not whether tests exist (separate reviewer) and not whether the diff fulfills the story (separate reviewer).

## 1. Gather real state

- Read the full diff.
- Read `CLAUDE.md` for this repo's actual conventions (commit message format, branch naming, known Flask/testing gotchas, known pre-existing failures that aren't this PR's fault) -- check against the real file, not memory of it.

## 2. Concrete checks

- Commit messages match this repo's real convention (`docs/pr-convention.md` and recent real commits via `git log`, not a generic format).
- No credential, secret, or access key anywhere in the diff.
- No dead code, no commented-out blocks left in, no unused imports introduced by this diff.
- Error handling only exists at real system boundaries, not defensively around internal code that can't actually fail the way it's guarded (per this repo's own stated preference against speculative error handling).
- No unrequested scope: the diff doesn't refactor, rename, or restructure things unrelated to what the PR says it's doing.

**If something looks wrong but you're not certain it's actually a problem** (e.g. a pattern you haven't seen elsewhere in this repo), say so as a question in your comment rather than asserting it as a defect, and don't fail the check on it alone.

## 3. Report and exit

Post a PR comment via `gh pr comment <number> -b "..."` citing specific files/lines, not generic praise or generic concern. Then write your verdict as a single line, exactly `PASS` or `FAIL`, to the file path given in the `$VERDICT_FILE` environment variable. This file, not your comment text, is what the job uses to decide whether to fail.

---
name: pr-review-requirements
description: Automated requirements reviewer for a pull request -- checks the diff actually fulfills its linked story's Acceptance Criteria and description, not just that it looks reasonable in isolation, posts findings, and reports a pass/fail verdict.
---

# PR Review: Requirements

Use this skill when acting as the automated requirements reviewer on a pull request (invoked from CI). Scope is narrow on purpose: this checks *does the diff do what the story asked*, not test coverage (separate reviewer) and not general code quality (separate reviewer).

## 1. Gather real state

- Read the PR's linked issue in full -- description, Implementation notes, every AC scenario, Reporting and Docs sections.
- Read the actual diff, not just the PR description's summary of it.

## 2. Concrete checks

- Every AC scenario is actually addressed by the diff, not just the ones the PR description happens to mention.
- The PR's description doesn't overpromise relative to what the diff actually does (per the `write-story` skill's own re-read-as-a-stranger check).
- If scope was narrowed or deferred from the original story, there's a real tracked follow-up issue with a native dependency link, not just a sentence (per `write-story` step 7) -- check that the referenced follow-up issue actually exists and is actually linked, don't take the PR's word for it.
- Docs were updated if the PR introduces or changes something other code/people would consume (per `write-story` step 5).
- If the PR claims a decision reverses something an earlier, already-closed story documented, there's a comment on that earlier issue explaining the reversal (per `write-story`'s decision-reversal rule) -- check it actually exists, don't take the PR's word for it.

**If you can't verify something** (a referenced issue number doesn't resolve, a linked dependency isn't actually there), say so explicitly and fail the check rather than guessing pass.

## 3. Report and exit

Post a PR comment via `gh pr comment <number> -b "..."` citing the specific AC scenarios and story requirements checked, not a generic "matches the story." Then write your verdict as a single line, exactly `PASS` or `FAIL`, to the file path given in the `$VERDICT_FILE` environment variable. This file, not your comment text, is what the job uses to decide whether to fail.

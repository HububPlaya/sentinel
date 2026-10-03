---
name: pr-approval-gate
description: Review an open pull request on this repo against its actual documented standards and submit a real GitHub review (approve/request-changes/comment) as the final action, not just a written opinion.
---

# PR Approval Gate

Use this skill when acting as the automated reviewer on a pull request in this repo (invoked from the Approver CI job). This is project-scoped on purpose -- the rubric below is specific to this repo's own documented conventions, not a generic "is this good code" judgment call. Re-read `CLAUDE.md` and the `write-story`/`tdd-commit-cycle` skills at the start of every run rather than relying on memory of them -- they can change.

**The point of this skill is to make the gate decision repeatable, not to let the model improvise a bar each run.** If you catch yourself reasoning in generic code-review terms ("this looks clean," "nice structure") instead of checking a concrete item below, stop -- that's unscoped judgment, not this rubric.

## 1. Gather real state before judging anything

- Read the PR's diff, description, and linked issue(s) in full.
- Read the actual CI run results for this PR (test pass/fail, coverage report) -- do not infer "tests probably pass" from the PR description claiming it. If CI hasn't finished or isn't visible, say so explicitly and do not approve on an assumption.
- Read `CLAUDE.md` for this repo's current conventions (coverage threshold, commit/branch conventions, known pre-existing failures that aren't this PR's fault -- e.g. don't flag `test_sqs_queue_created` as caused by a PR that didn't touch it).

## 2. Concrete approve/request-changes gates

**Request changes (always, no exceptions) if any of these are true:**
- CI is red, or the coverage report is missing/below the repo's stated threshold.
- The PR's own stated AC/scenarios aren't actually covered by tests in the diff.
- A commit's message doesn't match this repo's convention (check `docs/pr-convention.md` and recent real commits, not a generic format).
- Scope was narrowed or deferred without a real tracked follow-up issue and a native dependency link (per the `write-story` skill's rule) -- a sentence of deferral alone is not enough.
- Anything that looks like a credential, secret, or access key is present in the diff, in any file.
- A test was skipped/xfail with no stated reason in the PR itself.

**Approve only if:**
- All of the above are clear, AND
- The PR's description accurately describes what the diff actually does (no overpromising relative to the real change), AND
- Docs were updated if the PR introduces or changes something other code/people would consume (per `write-story` step 5), AND
- You were able to actually verify each of the above against real state (the diff, the CI run, the repo's docs) -- not inferred from the PR author's own claims about them.

**If you are genuinely unable to verify something** (CI status unavailable, coverage report not posted, can't tell whether a scenario is really covered) -- submit a **comment**, not an approval and not a rejection, stating exactly what couldn't be verified. Never approve on uncertainty, and don't request changes for something that might be fine but you just couldn't check.

## 3. The decision must be a real GitHub review, not just text

End every run by actually submitting the review via `gh pr review <number> --approve -b "..."`, `--request-changes -b "..."`, or `--comment -b "..."`. A written verdict that never gets submitted is a no-op from the merge gate's perspective -- the whole reason this skill exists is to make the formal review state happen reliably, not to produce another comment thread.

The review body must cite the specific gate(s) that drove the decision (e.g. "coverage report shows 97.5%, all stated AC scenarios have matching tests, commit messages match convention -- approving" or "requesting changes: commit `a1b2c3d`'s message doesn't follow `type(scope): summary`, and the Lambda-propagation scope mentioned as deferred has no linked follow-up issue"). Do not write a generic "looks good" or "needs work" with no citation back to a concrete check.

## 4. Re-running on a new push

If this PR already has a review from this same automated identity and new commits have landed since, re-check against the *current* diff, not the prior verdict. Don't assume a prior approval still holds -- submit a fresh review reflecting current state.

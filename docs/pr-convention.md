# Pull request convention

## Branch naming

Same `type/short-kebab-case-description` shape as everything else in this convention:

```
type/short-kebab-case-description
```

- `type` — same set as commit/PR types: `feat`, `fix`, `docs`, `refactor`, `chore`
- description — a few words, kebab-case, no trailing punctuation, describing the change (not
  the ticket number or your name)

Examples:
- `fix/eb-application-shared-across-environments`
- `feat/resource-pipeline`
- `docs/pr-convention`

**Note on existing branches:** the working branch for this project's early history used
`feature/...` (the long form) before this convention was written down — that's a legacy name,
not the pattern to copy. New branches use the short `feat/` form, matching commit types exactly,
so a branch name, its PR title, and its commits all use the same vocabulary.

## Title

Same format as commit titles: **Conventional Commits** —

```
type(scope): short summary
```

- `type` — `feat`, `fix`, `docs`, `refactor`, `chore` (same set used for commits)
- `scope` — the component the PR is mainly about (`elastic-beanstalk`, `pipeline`, `snack-recommender`)
- Lowercase, imperative mood ("add", not "added"), no trailing period

If a PR bundles more than one logical change (it usually shouldn't — see below), title it after
the most significant one and let the description's changelog cover the rest.

Examples:
- `feat(pipeline): add resource pipeline and multi-env promotion`
- `fix(elastic-beanstalk): parameterize IAM naming by app_name`
- `docs: document PR convention`

## Description

Use the template in `.github/PULL_REQUEST_TEMPLATE.md` — GitHub pre-fills it automatically when
you open a PR. It has four sections:

1. **Summary** — one to three sentences: what changed and why.
2. **Changes** — bullet list of the substantive changes. Keep this short; the real detail
   belongs in a journal entry, not duplicated here.
3. **Journal entries** — link the `docs/journal/.../*.md` entry (or entries) covering this
   work. This is the primary place detailed reasoning, bugs hit, and fixes live — the PR
   description points at them rather than repeating them.
4. **Testing** — how this was actually verified before opening the PR (`cdk diff` output
   reviewed, deployed to `dev` and confirmed healthy, pipeline run watched end to end, etc.).
   Matches the project's existing habit of testing before committing — this section makes that
   verification visible in the PR itself, not just in a journal entry no reviewer necessarily
   opens.

## One PR, one logical change

Keep PRs scoped the same way commits already are — one coherent piece of work, not an
accumulation of unrelated changes. If a working session touches both `infra/` and `pipeline/`
for genuinely separate reasons, that's two PRs, matching the existing practice of separate
commits per concern.

## Merge strategy: use "Merge commit," not "Squash and merge"

Journal entries reference specific commit hashes (`commit: <hash>` in each entry's frontmatter).
Squash-merging rewrites those commits into a single new hash on `main`, silently breaking every
journal entry's reference. Use GitHub's **"Merge commit"** option so the original commits — and
the hashes already written into the journal — stay reachable and accurate.

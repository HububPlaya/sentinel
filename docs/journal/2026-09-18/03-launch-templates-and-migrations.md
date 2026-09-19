---
date: 2026-09-18
sequence: 03
commit: <fill in after committing>
---

# Launch Configuration deprecation, and real migrations via Flask-Migrate

## A fourth, completely unrelated bug -- found only because of a full environment rebuild

After the KMS fix, `dev`'s environment stayed stuck at `502`/no real instances, even after a
manual EC2 instance termination. Chased this through several rounds of stale-vs-fresh log
confusion (a `web.stdout.log` that turned out to be genuinely frozen since the original crash,
not evidence of a recurring one) before doing a full EB "Rebuild environment" -- which is what
actually surfaced the real cause:

```
The Launch Configuration creation operation is not available in your account.
Use launch templates to create configuration templates for your Auto Scaling groups.
```

AWS deprecated EC2 Launch Configurations for new accounts as of October 1, 2024. This account
apparently falls under that restriction. The *original* environment kept working all day because
its existing launch configuration, created earlier, was still usable -- the restriction only
blocks *creating new* ones, which a full Rebuild does but routine deploys never touch. Confirmed
via AWS's own migration docs and fixed with one explicit option setting,
`DisableIMDSv1=true` under `aws:autoscaling:launchconfiguration`, which tells EB to provision via
a Launch Template instead -- also a genuine security improvement (IMDSv2-only blocks a known
SSRF credential-theft vector), not purely a workaround. `dev`'s stack was in `CREATE_FAILED` from
the rebuild attempt; fixed with a clean `cdk destroy` + `cdk deploy`, which then succeeded and
correctly used a Launch Template from the start.

Real lesson: a full instance replacement and a full environment rebuild are not equivalent tests
-- the rebuild exercised a code path (creating brand-new Auto Scaling resources) that nothing
today had actually exercised before, and that's exactly where this had been hiding.

## After recreation: the environment initially served EB's sample app, correctly

Recreating `EnvironmentStack` from scratch means a fresh `CfnEnvironment` with no `version_label`
-- exactly the documented, intentional behavior from `AppBundle`'s removal. Not a bug; resolved
by re-triggering the app pipeline, which deployed the real code and app-set environment variables
onto the fresh environment.

## The real remaining gap, finally reached: schema never created

With the full chain working, `/snacks` failed with `relation "snacks" does not exist` --
confirmed via logs, not assumed. This was the correct, best-case failure: it meant the entire
connection chain (EB -> Secrets Manager -> KMS -> RDS) worked end to end; only the schema itself
was missing, since `db.create_all()` had never run against real Postgres.

Discussed wiring `db.create_all()` into app startup as a quick fix, but a follow-up question
("how do we solve schema evolution on existing tables?") made clear that a real solution was
worth doing now rather than deferring again -- `create_all()` can create missing tables but can
never alter existing ones, so it was never going to solve the actual long-term problem, only the
immediate one.

## Adopted Flask-Migrate (Alembic) instead

- `db.create_all()` removed entirely from the app -- replaced by real, versioned migrations.
- New `.platform/hooks/predeploy/01_migrate.sh` runs `flask db upgrade` automatically before
  every deploy, on every environment -- the schema-creation step that had to be manually
  remembered for `dev` and `test` today never has to happen manually again, for any environment,
  including `stage`/`prod` whenever they first deploy.
- Generating the initial migration locally hit one real snag: Alembic reported "No changes in
  schema detected" against the local SQLite file, because that file already had the full schema
  from earlier testing (predating this change, back when `init-db` used `create_all()`). Not a
  bug -- Alembic was correctly comparing models against a database that already matched them.
  Fixed by deleting the stale local `.db` file so the migration was generated against a genuinely
  empty database, matching what `dev`/`test`'s real (empty) RDS instances actually look like.
- Generated migration reviewed by hand before trusting it -- confirmed it correctly captures all
  three tables' columns, the `cuisine_type` index, the `email` uniqueness, both foreign keys, the
  `(user_id, snack_id)` uniqueness, and the `1 <= rating <= 5` check constraint.
- `migrations/` is committed to the repo -- it's the actual source of truth for schema history
  going forward, not generated/ignorable output.

## Next up (not yet started)

- Confirm the predeploy hook actually works on a real EC2 instance (local success doesn't prove
  this, same lesson as everything else today) -- still pending as of this entry.
- The `DisableIMDSv1` fix (from `fix/eb-launch-template-migration`) still needs to reach `test`
  and `stage` via the resource pipeline, so neither hits the same Launch Configuration wall the
  next time either needs a rebuild.
- Seeding real data on `dev`/`test` is still a manual, separate step (`seed-db` deliberately
  doesn't run automatically) -- no current mechanism to run it against the real databases without
  SSH/exec access.
- HTTPS on the load balancer.

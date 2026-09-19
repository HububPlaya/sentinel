# How RDS is provisioned, and what it doesn't cover yet

`infra/infra/rds/` provisions one Postgres RDS instance per environment, fully independent of
Elastic Beanstalk. See `docs/infra-overview.md` for where this fits among the other stacks, and
`docs/elastic-beanstalk/deploy-flow.md` for how EB actually connects to it.

## What's built

- **One primary instance per environment** (`dev`/`test`/`stage`/`prod`), each with its own RDS
  instance, own security group, own KMS key -- full isolation, deliberately, so nothing in one
  environment's database can be affected by another's.
- **Encryption at rest via a customer-managed KMS key**, not the AWS-managed default -- gives
  control over rotation (`enable_key_rotation=True`) and lets the same key also protect the
  Secrets Manager credential (a genuine two-consumer case, which is specifically why this key was
  extracted into its own construct rather than left inline).
- **Credentials in Secrets Manager**, auto-generated (`Credentials.from_generated_secret`) --
  never appear in CDK code, environment variables, or console output. The app fetches them at
  startup via `boto3`, using the EB instance role's scoped `secretsmanager:GetSecretValue` +
  `kms:Decrypt` grants (see `docs/journal/2026-09-18/01-rds-and-eb-security-group-fix.md` and
  `02-connect-app-to-rds.md` for how both of those were actually wired and debugged).
- **A read replica on all four environments** -- built specifically to demonstrate the pattern,
  not because this app has a real read-scaling need. Worth being explicit about that distinction;
  see "Known limitations" below for what this means practically.
- **Two basic CloudWatch alarms** (high CPU, low free storage) -- visible in the console, no
  notification action wired up.
- **Real schema migrations via Flask-Migrate/Alembic**, applied automatically on every deploy via
  `.platform/hooks/predeploy/01_migrate.sh` in the app itself -- see
  `docs/journal/2026-09-18/03-launch-templates-and-migrations.md`.

## Design decisions worth knowing before changing anything here

- **`DatabaseStack` has zero knowledge of EB.** Access is granted at the composition root
  (`app.py`), via `allow_ingress_from(...)`, not baked into the stack's constructor -- so it stays
  independently deployable and reusable by any future consumer, not just EB.
- **Ingress rules and the secret/KMS grants are created inside `EnvironmentStack`'s scope, not
  `DatabaseStack`'s.** `EnvironmentStack` already legitimately imports from `DatabaseStack` (the
  DB host, the secret ARN); if `DatabaseStack` also had to import back from `EnvironmentStack`,
  the two stacks would depend on each other and CDK couldn't resolve a deploy order. Hit this
  exact circular-dependency shape twice (the ingress rule, then separately the KMS grant) before
  settling on this pattern -- worth keeping in mind before reaching for a `grant_*()` convenience
  method here, several of which modify the *target* resource's policy, not just the grantee's.

## Known limitations and concerns

Written down deliberately, since none of this was documented anywhere until now.

- **Public subnets, not private isolated ones.** RDS sits in the default VPC's public-address
  subnets (`vpc_subnets=PUBLIC`), relying entirely on `publicly_accessible=False` plus the
  security group for isolation -- not genuine network-level isolation. A future misconfiguration
  (someone flips `publicly_accessible` to `True`, or a security group rule gets loosened) would
  expose it directly to the internet, with no second layer of defense. The more defensible design
  is `PRIVATE_ISOLATED` subnets in a custom VPC (no NAT gateway needed either, since RDS needs no
  outbound internet access) -- not built here, specifically to avoid taking on a custom VPC as new
  infrastructure to manage. Worth revisiting if this project's security bar needs to go up.
- **Backups are configured but never tested.** `backup_retention_days` is set per environment,
  but no restore has ever actually been attempted. A backup nobody has restored from is really
  just a hope, not a verified capability.
- **CloudWatch alarms have no notification action.** They'll show `ALARM` in the console, but
  nothing pages anyone. Wiring up SNS/email/Slack is real, explicitly deferred work.
- **Credentials never rotate.** Secrets Manager supports automatic rotation via a Lambda function;
  none is configured. The generated password is set once, at creation, and stays static
  indefinitely.
- **Destroying a non-prod `DatabaseStack` genuinely destroys the KMS key and the database.**
  `RemovalPolicy.DESTROY` applies to every environment except `prod` (`deletion_protection=False`
  for `dev`/`test`/`stage`). This is intentional -- but worth remembering before ever running
  `cdk destroy` against one of these stacks for a reason other than "I want this gone for good."
- **The read replica is genuinely unused.** `DATABASE_READ_URL` is exposed in the app's config
  but nothing routes any query to it. Running it on all four environments was a deliberate choice
  to demonstrate the pattern, not a response to real load -- worth being honest about that if this
  project ever comes up in a context where the distinction matters.
- **Local development never touches real RDS at all.** The SQLite fallback means every RDS-side
  bug found today (the security group config, the region resolution, the KMS grant) was
  structurally invisible to local testing, by design -- there is no way to shrink that gap without
  either opening RDS to a local IP (undesirable) or maintaining a real, separate always-on dev
  database reachable from a laptop (not currently worth the complexity).
- **RDS's instance placement isn't AZ-pinned the way EB's is.** `EnvironmentStack` explicitly
  selects AZs (`us-east-1e` in this account doesn't support `t3` instance types for EC2, confirmed
  by a real failure) -- `DatabaseStack` doesn't apply the same restriction to RDS's own AZ
  placement. RDS and EC2 don't necessarily share the exact same per-AZ instance-type support
  matrix, so this is an unverified, plausible future failure mode, not a confirmed one.

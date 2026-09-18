---
date: 2026-09-18
sequence: 01
commit: 2767391
---

# RDS built, EB security group bug hunted to its real cause

## RDS submodule built, mirroring elastic_beanstalk/'s shape

New `infra/infra/rds/` submodule: `DatabaseConfig`/`DATABASE_CONFIGS` (per-environment sizing,
same pattern as `EnvConfig`), and constructs — `DatabaseInstance`, `DatabaseReadReplica`,
`DatabaseEncryptionKey`, `DatabaseAlarms` — composed by `DatabaseStack`.

Decisions made along the way:
- **Full isolation** — one RDS instance per environment (`dev`/`test`/`stage`/`prod`), not
  shared between `dev`/`test`, despite the extra cost, to preserve the same lifecycle isolation
  already established for EB environments.
- **Credentials via Secrets Manager**, not a plain env var — `rds.Credentials.from_generated_secret(...)`,
  never a password in CDK code or plaintext config.
- **Read replicas on all four environments** — deliberately built to demonstrate the pattern,
  not because this app has a real read-scaling need. Worth being explicit about that distinction
  rather than implying otherwise.
- **Encryption at rest** — confirmed `storage_encrypted` defaults to `False` in CDK unless a key
  is explicitly provided; fixed by adding a customer-managed KMS key.
- **Two basic CloudWatch alarms** (high CPU, low free storage) — no notification action wired up
  yet; that's real future work, not part of "basic."

## Decoupling fix: allow_ingress_from(), not a required constructor argument

First draft had `DatabaseStack` requiring `allowed_security_group` at construction time —
correctly flagged as backwards for something meant to be independently deployable, since it
baked "there is exactly one consumer, and it's EB" into the database's own existence. Fixed by
having `DatabaseInstance`/`DatabaseReadReplica` expose `allow_ingress_from(peer, description)`,
called from `app.py` after both stacks exist, rather than the database requiring a consumer to
be named before it can be built at all. `DatabaseStack` on its own now has zero knowledge of EB.

## KMS extracted into its own construct; alarms deliberately left bundled

Applied one consistent test to both: is there a genuine current second *consumer*, not just a
second instance of the same kind of thing. KMS: yes — the same key needed to encrypt both RDS
storage and the Secrets Manager credential, a real two-consumer case within `DatabaseStack`
today, confirmed `Credentials.from_generated_secret(..., encryption_key=...)` accepts this.
Alarms: no — both alarms share the same lifecycle, no cross-consumer reuse, so bundling them in
one `DatabaseAlarms` construct (same precedent as `ElasticBeanstalkInstanceRole` bundling a role
+ instance profile) stays correct; splitting per-alarm would have been ceremony without a reason.

## Two real circular-dependency bugs, same underlying cause

`cdk synth` failed twice with `DependencyCycle` errors, both for the same reason: a CDK
convenience method (`add_ingress_rule`, then separately `secret.grant_read()`) modified a
resource in `DatabaseStack`'s own template in a way that required importing something from
`EnvironmentStack` — while `EnvironmentStack` already legitimately imports from `DatabaseStack`
(the DB host, the secret ARN). Two stacks each needing the other creates a cycle CDK can't
resolve. Fixed both by moving the resource creation into whichever stack already had the correct
import direction (`environment_stack`'s scope) instead of using the higher-level grant helpers
that silently created the reverse edge. General lesson: check whether a CDK "grant"/convenience
method touches the *other* resource's template, not just the grantee's, before assuming it's a
one-directional import.

## InstanceRole rename collided with an already-deployed resource

Renaming `WebAppInstanceRole` → `ElasticBeanstalkInstanceRole` earlier also changed the
**construct ID** (not just the class name), which changed the CloudFormation logical ID.
Since the *physical* name (`snack-recommender-eb-ec2-role-dev`) is explicit, not
auto-generated, CloudFormation tried to create a new resource under the old resource's still-held
name — a real `NAME_CONFLICT_VALIDATION_ERROR`. Fixed by destroying and recreating `dev`'s
`EnvironmentStack` fresh. Preemptively destroyed `test`'s and `stage`'s `EnvironmentStack`s too,
since they were deployed under the same old logical ID and would hit the identical conflict the
next time the resource pipeline ran `Deploy_test`/`Deploy_stage` — better to clear it manually
than let the pipeline discover it.

## The EB "security group does not exist" bug — three theories, one of them wrong

Real failure, hit repeatedly: `CfnEnvironment` creation failing with
`The security group 'sg-...' does not exist`, even though the security group demonstrably
existed (created successfully in the same or an earlier stack).

**Theory 1 (correct diagnosis of a smell, wrong root cause): propagation lag.** Three consecutive
failures all showed the same ~2–2.5 minute gap between the security group's `CREATE_COMPLETE`
and EB's environment creation attempting to use it, regardless of how much real time passed
between separate deploy attempts (hours, in one case). Built a Lambda-backed custom-resource
wait construct as a fix.

**Reconsidered before implementing:** questioned why a time delay was necessary at all — correct
instinct. Identified the real smell: the security group's lifecycle was coupled to
`EnvironmentStack`, which gets destroyed/recreated far more often than the security group itself
needs to. Extracted `NetworkStack` to own it independently. Deep-searched for confirmation:
found AWS's own re:Post guidance explicitly recommending "create your own security groups
independently... to avoid lifecycle dependencies" for a related EB security-group problem, and
found the general "separate networking stack from application stack" pattern is textbook
AWS/CloudFormation best practice, independent of this specific bug. Deleted the Lambda-wait
construct as unnecessary given the structural fix.

**Test disproved the theory:** deployed `NetworkStack` alone, waited ~10 minutes before
referencing it (far longer than the ~2 minute gap that failed three times) — **identical
failure anyway.** This directly disproved "it just needs more time," at any interval. Important
moment: the theory had real supporting evidence (consistent timing, an official-sounding
mechanism, AWS's own stabilization-wait documentation excluding `EC2::SecurityGroup`) and was
still wrong. Worth remembering that plausible, well-evidenced theories still need to survive an
actual reproduction test before trusting them.

**Real root cause, found by re-examining AWS's own re:Post article more carefully:** EB
environments only accept security group *IDs* when explicitly VPC-configured
(`aws:ec2:vpc/VPCId` set); without that, EB treats the environment as non-VPC-configured and
expects security group *names*. `ElasticBeanstalkEnvironment` never set any `aws:ec2:vpc`
namespace option settings — an existing gap that simply never surfaced until a *custom* (ID-only)
security group replaced EB's auto-managed one. Fixed by adding explicit `VPCId`, `Subnets`, and
`ELBSubnets` option settings, confirmed against multiple independent sources (Pulumi's docs, a
real AWS sample template, and a full EB option-namespace reference) before implementing, given
the day's earlier guessed-API mistakes.

**A second, real bug surfaced immediately after fixing the first:** `Your selected instance
types (t3.micro) aren't available in your selected VPC Subnets` — `us-east-1e` in this account
doesn't support `t3` instances (AWS randomizes each account's AZ name-to-physical mapping, so
this is account-specific, not universal). Initially fixed with a positional slice
(`vpc.public_subnets[:2]`); correctly flagged as fragile and implicit. Replaced with
`vpc.select_subnets(availability_zones=[...])`, explicit AZs sourced from config.

**Config placement reconsidered:** briefly extracted a standalone `NetworkConfig` dataclass for
the one `availability_zones` field, then reversed it — same test as the `ENVIRONMENT_NAMES`
reversal a few days ago: a dataclass for a single field with no current per-environment variation
isn't earning its own module yet. Folded `availability_zones` directly into `EnvConfig`.

## Confirmed working

Full deploy sequence (`Application` → `Network` → `Database` → `Infra`) for `dev` succeeded end
to end. `Environment` reached `CREATE_COMPLETE` for the first time after four prior failures.
`describe-environments` confirmed `Ready`/`Green`.

## Next up (not yet started)

- The Flask app still reads `DATABASE_URL` as one plain env var — needs updating to fetch
  credentials from Secrets Manager at runtime and assemble the real connection string from
  `DB_HOST`/`DB_PORT`/`DB_NAME`/`DB_SECRET_ARN`.
- `test` and `stage` still need their `EnvironmentStack`s (and now their `Network`/`Database`
  stacks, first time ever) deployed via the resource pipeline — not yet re-run since the
  VPC/AZ fixes landed.
- HTTPS on the load balancer.
- Real tests replacing the app pipeline's Build-stage placeholder.
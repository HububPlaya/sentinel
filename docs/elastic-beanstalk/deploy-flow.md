# How this deploys an app to Elastic Beanstalk

This walks through what actually happens, from config selection down to a running EC2 instance
connected to a real database, and separately, how real app code gets onto that instance.

## Four stacks, four different lifecycles

- **`ApplicationStack`** — the EB Application (a single, account-wide container). Deployed
  **once, ever**.
- **`NetworkStack`** — the EB security group. Deployed once per environment, **rarely touched**
  afterward. Exists as its own stack specifically so it isn't destroyed/recreated every time
  `EnvironmentStack` is (which happens often) — see
  `docs/journal/2026-09-18/01-rds-and-eb-security-group-fix.md`.
- **`DatabaseStack`** — the RDS instance (+ optional read replica). Deployed once per
  environment, independent of everything else — has no knowledge of EB at all.
- **`EnvironmentStack`** — the EB Environment itself (EC2, load balancer, ASG) + its IAM role.
  Deployed once per environment; the one that changes most often.

Earlier versions had one stack create the Application per environment (every environment tried
`CreateApplication` with the same name — always failed after the first) and had the security
group living inside `EnvironmentStack` (destroyed/recreated every time that stack was, which
turned out to be irrelevant to a real bug that was actually a missing VPC configuration — see
the journal entry above for the full story, including two disproven theories along the way).

## 1. Config defines what each environment looks like

`elastic_beanstalk/config/environment.py` holds one `EnvConfig` per environment, built from:

- `scaling.py` → `AutoScalingConfig` — min/max instance count
- `instance.py` → `InstanceConfig` — instance type (defaults to `t3.micro`)
- `iam.py` → `IamConfig` — suffixes for the IAM role/instance profile
- `availability_zones` (a field on `EnvConfig` itself) — explicit AZs to deploy into. Not every
  AZ in an account supports every instance type (AWS randomizes each account's AZ
  name-to-physical mapping) — `us-east-1e` in this account doesn't support `t3`, confirmed by a
  real deploy failure. Defaults to `["us-east-1a", "us-east-1b"]`.

`rds/config/database.py` holds one `DatabaseConfig` per environment — instance class, storage,
Multi-AZ, deletion protection, backup retention, whether to create a read replica.

## 2. `app.py` composes all four stacks and wires access between them

```python
application_stack = ApplicationStack(app, "SnackRecommenderApplication", app_name=APP_NAME, env=env)

network_stack = NetworkStack(app, f"SnackRecommenderNetwork-{target_env}", app_name=APP_NAME, env_name=target_env, env=env)

database_stack = DatabaseStack(app, f"SnackRecommenderDatabase-{target_env}", app_name=APP_NAME, env_name=target_env, config=DATABASE_CONFIGS[target_env], env=env)

environment_stack = EnvironmentStack(
    app, f"SnackRecommenderInfra-{target_env}",
    app_name=APP_NAME, env_config=env_config,
    security_group=network_stack.security_group,
    app_environment_variables={  # DB_HOST, DB_PORT, DB_NAME, DB_SECRET_ARN, DB_READ_HOST
        ...
    },
    env=env,
)

environment_stack.add_dependency(application_stack)

# Access is granted HERE, at the composition root — neither DatabaseStack nor
# NetworkStack knows about EB at construction time.
ec2.CfnSecurityGroupIngress(environment_stack, "AllowDbIngressFromEb", ...)
environment_stack.instance_role.role.add_to_policy(...)  # secretsmanager:GetSecretValue
```

Since more than one stack now exists, every `cdk` command needs an explicit stack name.

**Why access is granted in `app.py`, not inside `DatabaseStack`:** an early draft had
`DatabaseStack` require an `allowed_security_group` parameter at construction — backwards for
something meant to be independently deployable, since it baked "there is exactly one consumer"
into the database's own existence. Fixed by having `DatabaseInstance`/`DatabaseReadReplica`
expose `allow_ingress_from(peer, description)`, called from `app.py` once both stacks exist.
`DatabaseStack` on its own has zero knowledge of EB.

**A real constraint this creates:** the ingress rule and the secret-read policy are created
inside `environment_stack`'s scope, not `database_stack`'s — `EnvironmentStack` already
legitimately imports from `DatabaseStack` (the DB host, the secret ARN), so anything that would
force `DatabaseStack` to import back from `EnvironmentStack` creates a circular dependency CDK
can't resolve. Hit this twice (once via `add_ingress_rule`, once via `secret.grant_read()`) —
both fixed by creating the resource in the stack that already has the correct import direction.

## 3. `ApplicationStack` and `NetworkStack` — deployed once, rarely touched again

```python
# ApplicationStack
self.application = ElasticBeanstalkApplication(self, "Application", app_name=app_name)

# NetworkStack
self.eb_security_group = ElasticBeanstalkSecurityGroup(self, "SecurityGroup", vpc=self.vpc, ...)
```

Both expose a stable reference (`self.application`, `self.security_group`) for other stacks to
import, and neither is ever recreated just because `EnvironmentStack` is.

## 4. `DatabaseStack` — fully independent

Creates a KMS key (shared by RDS storage encryption and the Secrets Manager credential — a real
two-consumer case, unlike the two CloudWatch alarms which stay bundled in one construct since
they don't have that kind of reuse), the primary RDS instance, optionally a read replica, and
two basic alarms. Does its own VPC lookup. No parameter anywhere references EB.

## 5. `EnvironmentStack` composes the IAM role and the EB Environment

```python
self.instance_role = ElasticBeanstalkInstanceRole(self, "InstanceRole", app_name=app_name, ...)

self.eb_environment = ElasticBeanstalkEnvironment(
    self, "Environment",
    app_name=app_name, env_config=env_config,
    instance_profile_name=self.instance_role.instance_profile.ref,
    security_group_id=self.security_group.security_group_id,  # from NetworkStack, passed in
    vpc=self.vpc,
    app_environment_variables=app_environment_variables,
)
```

Note `.ref`, not `.instance_profile_name` — a real CloudFormation token, so CFN tracks the
dependency automatically rather than relying on a plain string matching up correctly.

## 6. `ElasticBeanstalkInstanceRole` creates what EC2 needs to run at all

An IAM role trusting `ec2.amazonaws.com`, the two AWS-managed EB policies, and an instance
profile — named from `app_name` + a suffix, so renaming the app never requires touching `iam.py`.

## 7. `ElasticBeanstalkEnvironment` creates the actual running environment — including VPC config that was missing for a long time

```python
selected = vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC, availability_zones=cfg.availability_zones)

option_settings = [
    OptionSettingProperty(namespace="aws:ec2:vpc", option_name="VPCId", value=vpc.vpc_id),
    OptionSettingProperty(namespace="aws:ec2:vpc", option_name="Subnets", value=",".join(subnet_ids)),
    OptionSettingProperty(namespace="aws:ec2:vpc", option_name="ELBSubnets", value=",".join(subnet_ids)),
    ...  # IamInstanceProfile, InstanceType, SecurityGroups, MinSize, MaxSize
]
```

**The `aws:ec2:vpc` settings are not decorative.** Without them, EB treats the environment as
non-VPC-configured and expects security group *names*, not *IDs* — passing a custom security
group's ID (as opposed to letting EB auto-manage its own) then fails with
`The security group 'sg-...' does not exist`, regardless of whether the group actually exists or
how long it's existed. This was a real, reproduced bug — confirmed via a deliberate test (10
minutes of wait time, still failed identically) that ruled out a propagation-timing explanation
that initially looked plausible. Full story in
`docs/journal/2026-09-18/01-rds-and-eb-security-group-fix.md`.

`select_subnets(availability_zones=...)` is used deliberately instead of slicing the subnet list
positionally — explicit and self-documenting, not dependent on incidental ordering.

**No `version_label` is set here.** A freshly created environment serves EB's default sample app
until the app pipeline's first real deploy to it — expected, not a bug.

## 8. Getting real code onto an environment — the app pipeline, not `cdk deploy`

Ongoing code deploys are owned by the app pipeline (`pipeline/`, `PipelineStack`) — builds once,
promotes through `dev → test → [approval] → stage → [approval] → prod` via Elastic Beanstalk's
native CodePipeline deploy action, calling the EB API directly — not through CloudFormation.
`cdk deploy` on `EnvironmentStack` never needs to know or care what code is currently running.
An earlier `AppBundle` construct existed for bootstrapping a new environment with code already
on it; it's since been removed entirely, fully superseded by the app pipeline.

## 9. Ordering the pipeline relies on, not something CDK enforces across stacks

`Network` and `Database` have no dependency on each other. `Environment` depends on both (via
real cross-stack references CDK does track) and on `Application` (via an explicit
`add_dependency`, since that link is only a matching string, not a generated value). The
resource pipeline deploys, per environment: `[Network, Database, Environment]` (plus
`Application`, once, for `dev`) — sequencing the pipeline's stages respect, not something
CloudFormation enforces across genuinely separate stacks on its own.

## Command reference

```
cdk synth                                     # generate all stack templates, no AWS calls
cdk deploy SnackRecommenderApplication        # once, ever
cdk deploy SnackRecommenderNetwork-dev        # once per environment, rarely again
cdk deploy SnackRecommenderDatabase-dev       # once per environment
cdk deploy SnackRecommenderInfra-dev          # the one that changes most often
cdk destroy SnackRecommenderInfra-test        # tear down one environment (Network/Database untouched)
```
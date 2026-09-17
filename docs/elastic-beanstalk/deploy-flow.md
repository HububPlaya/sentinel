# How this deploys an app to Elastic Beanstalk

This walks through what actually happens, in order, when you run `cdk deploy -c env=dev` —
from config selection down to a running EC2 instance.

## 1. Config defines what each environment looks like

`config/environment.py` holds one `EnvConfig` per environment (`dev`, `test`, `stage`, `prod`),
each built from three smaller pieces:

- `scaling.py` → `AutoScalingConfig` — min/max instance count for that environment
- `instance.py` → `InstanceConfig` — instance type (defaults to `t3.micro`)
- `iam.py` → `IamConfig` — base names for the IAM role/instance profile

```python
ENVIRONMENTS = {
    "dev":   EnvConfig(env_name="dev",   scaling=AutoScalingConfig(1, 1)),
    "test":  EnvConfig(env_name="test",  scaling=AutoScalingConfig(1, 2)),
    "stage": EnvConfig(env_name="stage", scaling=AutoScalingConfig(2, 4)),
    "prod":  EnvConfig(env_name="prod",  scaling=AutoScalingConfig(2, 6),
                        instance=InstanceConfig(instance_type="t3.small")),
}
```

This dictionary is the only place environment sizing is defined. Nothing downstream hardcodes
instance counts or types.

## 2. `app.py` picks one environment

```python
target_env = app.node.try_get_context("env") or "dev"
env_config = ENVIRONMENTS[target_env]
```

The `-c env=dev` flag on the CLI is what selects which `EnvConfig` gets used. Same code path
for every environment — only the data changes.

## 3. `InfraStack` composes two constructs, in order

```python
self.instance_role = WebAppInstanceRole(self, "WebAppInstanceRole",
    env_name=env_config.env_name, iam_config=env_config.iam)

self.web_app_hosting = WebAppHosting(self, "WebAppHosting",
    app_name=app_name, env_config=env_config,
    instance_profile_name=self.instance_role.instance_profile.instance_profile_name)
```

The role is created first, because `WebAppHosting` needs its instance profile name as an input.

## 4. `WebAppInstanceRole` creates what EC2 needs to run at all

An EC2 instance can't do anything in AWS until it has permission to. This construct creates:

- An **IAM role** that EC2 instances are allowed to assume (`ec2.amazonaws.com` as the trusted
  principal)
- Two **AWS-managed policies** attached to it — `AWSElasticBeanstalkWebTier` and
  `AWSElasticBeanstalkMulticontainerDocker` — the same permission set EB's own console wizard
  attaches by default
- An **instance profile** wrapping that role, which is the actual thing EC2 launch
  configuration references

Without this, `cdk deploy` would fail — Elastic Beanstalk requires a valid instance profile to
launch any instance.

## 5. `WebAppHosting` creates the Elastic Beanstalk application and environment

Two separate AWS resources, created in order:

- **`CfnApplication`** — the logical container/project (`webapp`). This holds no compute by
  itself.
- **`CfnEnvironment`** — the actual running deployment. This is where the real provisioning
  happens: EB stands up an EC2 instance (or instances, per `AutoScalingConfig`), a load
  balancer, and a security group, using:
  - `solution_stack_name` to pick the OS/runtime image (Python 3.13 on Amazon Linux 2023)
  - `IamInstanceProfile` (passed in from step 4) so the instance has permission to run
  - `MinSize`/`MaxSize` from the environment's scaling config

The environment has an explicit `add_resource_dependency` on the application, so CloudFormation
creates them in the correct order.

## 6. What's actually running after deploy

Once `CREATE_COMPLETE` is reached, EB has a live EC2 instance behind a load balancer, reachable
at a generated URL (`<app>-<env>.<region>.elasticbeanstalk.com`, HTTP only — HTTPS isn't
configured yet). No app code has been pushed yet, so it's currently serving Elastic Beanstalk's
default sample app. That placeholder gets replaced once a real application version is deployed
into this same environment.

## Command reference

```
cdk synth -c env=dev       # generate the CloudFormation template locally, no AWS calls
cdk diff -c env=dev        # preview what would change
cdk deploy -c env=dev      # create/update the real resources
cdk destroy -c env=dev     # tear it down
```
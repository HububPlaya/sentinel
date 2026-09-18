# How this deploys an app to Elastic Beanstalk

This walks through what actually happens, from config selection down to a running EC2 instance,
and separately, how real app code actually gets onto that instance.

## Two separate things, two separate stacks

An Elastic Beanstalk **Application** is a single, account-wide container. An Elastic Beanstalk
**Environment** is the actual running thing (EC2, load balancer, ASG) — many Environments live
under one Application. Because of that, provisioning is split into two CDK stacks with very
different lifecycles:

- **`ApplicationStack`** — creates the Application. Deployed **once, ever**, not per-environment.
- **`EnvironmentStack`** (one per `-c env=` value) — creates one environment's IAM role and EB
  Environment. Requires the Application to already exist; never creates one itself.

Earlier versions of this project had one stack create both per environment, which meant every
environment tried to `CreateApplication` with the same name — the second one always failed.
See `docs/journal/2026-09-17/01-application-environment-separation.md` for the full story.

## 1. Config defines what each environment looks like

`elastic_beanstalk/config/environment.py` holds one `EnvConfig` per environment (`dev`, `test`,
`stage`, `prod`), each built from three smaller pieces:

- `scaling.py` → `AutoScalingConfig` — min/max instance count for that environment
- `instance.py` → `InstanceConfig` — instance type (defaults to `t3.micro`)
- `iam.py` → `IamConfig` — suffixes for the IAM role/instance profile (combined with `app_name`
  at construction time, not hardcoded)

```python
ENVIRONMENTS = {
    "dev":   EnvConfig(env_name="dev",   scaling=AutoScalingConfig(1, 1)),
    "test":  EnvConfig(env_name="test",  scaling=AutoScalingConfig(1, 2)),
    "stage": EnvConfig(env_name="stage", scaling=AutoScalingConfig(2, 4)),
    "prod":  EnvConfig(env_name="prod",  scaling=AutoScalingConfig(2, 6),
                        instance=InstanceConfig(instance_type="t3.small")),
}
```

This dictionary is the only place environment sizing is defined.

## 2. `app.py` always creates the Application, plus one Environment

```python
env = cdk.Environment(account=..., region=...)

ApplicationStack(app, "SnackRecommenderApplication", app_name="snack-recommender", env=env)

target_env = app.node.try_get_context("env") or "dev"
env_config = ENVIRONMENTS[target_env]

EnvironmentStack(
    app, f"SnackRecommenderInfra-{target_env}",
    app_name="snack-recommender", env_config=env_config, env=env,
)
```

Since `app.py` now always synthesizes two stacks, `cdk` commands need an explicit stack name —
a bare `cdk deploy -c env=test` will error once more than one stack exists.

## 3. `ApplicationStack` — deployed once

```python
self.application = ElasticBeanstalkApplication(self, "Application", app_name=app_name)
```

Creates a single `CfnApplication`. That's it. No dependency on any environment.

## 4. `EnvironmentStack` composes two constructs, for one environment

```python
self.instance_role = WebAppInstanceRole(self, "WebAppInstanceRole",
    app_name=app_name, env_name=env_config.env_name, iam_config=env_config.iam)

self.eb_environment = ElasticBeanstalkEnvironment(self, "Environment",
    app_name=app_name, env_config=env_config,
    instance_profile_name=self.instance_role.instance_profile.ref)
```

The role is created first, since `ElasticBeanstalkEnvironment` needs its instance profile as an
input. Note `.ref`, not `.instance_profile_name` — a real CloudFormation token, so CFN tracks
the dependency automatically rather than relying on a plain string matching up correctly.

## 5. `WebAppInstanceRole` creates what EC2 needs to run at all

- An **IAM role** trusting `ec2.amazonaws.com`
- Two **AWS-managed policies** — `AWSElasticBeanstalkWebTier`, `AWSElasticBeanstalkMulticontainerDocker`
- An **instance profile** wrapping that role

Role and profile names are built from `app_name` + a suffix, so renaming the app never requires
touching `iam.py`.

## 6. `ElasticBeanstalkEnvironment` creates the actual running environment

One `CfnEnvironment` — EC2 instance(s), a load balancer, an ASG — using:
- `solution_stack_name` — Python 3.13 on Amazon Linux 2023
- `IamInstanceProfile` from step 5
- `MinSize`/`MaxSize` from the environment's scaling config
- `application_name` — references the Application by name; assumes it already exists

**No `version_label` is set here.** A freshly created environment has none, and briefly serves
EB's default sample app — expected, not a bug. Getting real code onto it is a separate step
(next section), not something `EnvironmentStack` does.

## 7. Getting real code onto an environment — the app pipeline, not `cdk deploy`

`EnvironmentStack` only provisions the *shell*. Ongoing code deploys are owned by the app
pipeline (`pipeline/`, `PipelineStack`) — it builds the app once and promotes that artifact
through `dev → test → [approval] → stage → [approval] → prod` via Elastic Beanstalk's native
CodePipeline deploy action, calling the EB API (`CreateApplicationVersion`/`UpdateEnvironment`)
directly — not through CloudFormation.

This is deliberate: `cdk deploy` on `EnvironmentStack` should never need to know or care what
code is currently running. An `AppBundle` construct exists for one narrow, manual case —
bootstrapping a brand-new environment with real code already on it — but it is **not** wired
into `EnvironmentStack`'s routine deploys. If it were, every infra-only change (resizing an
instance, say) would fight the app pipeline's most recent deploy.

## 8. Ordering rule the pipelines rely on, not something CDK enforces

The Application must exist before any environment's first deploy. In practice: the resource
pipeline (`ResourcePipelineStack`) always deploys `dev` first — `["SnackRecommenderApplication",
"SnackRecommenderInfra-dev"]` — before `test`, `stage`, or `prod`, which each only deploy their
own `SnackRecommenderInfra-<env>`. This is a deployment-sequencing fact the pipeline is built to
respect, not something CloudFormation tracks as a resource dependency across separate stacks.

## Command reference

```
cdk synth                                  # generate templates for both stacks, no AWS calls
cdk diff SnackRecommenderApplication       # preview the Application stack
cdk diff SnackRecommenderInfra-dev         # preview one environment's stack
cdk deploy SnackRecommenderApplication     # create/update the Application (once, ever)
cdk deploy SnackRecommenderInfra-dev       # create/update one environment
cdk destroy SnackRecommenderInfra-test     # tear down one environment (Application untouched)
```
# Infrastructure Overview

Directory structure, as of the first successful `cdk deploy`:

```
sentinel/                              # repo root
  infra/                               # CDK project — provisions EB now, more AWS resources later
    .venv/
    cdk.out/
    infra/                             # Python package (named after the "infra/" folder — CDK convention)
      __init__.py
      elastic_beanstalk/               # one submodule per independently-deployable resource
        __init__.py
        application_stack.py           # owns the EB Application — deployed once, ever
        environment_stack.py           # owns one environment's IAM role + EB Environment
        config/
          __init__.py
          scaling.py
          instance.py
          iam.py                       # suffixes only — app_name is passed in, not hardcoded
          environment.py               # EnvConfig + ENVIRONMENTS + ENVIRONMENT_NAMES (inline —
        constructs/                    # extract to a shared module if a second consumer needs it)
          __init__.py
          app_bundle.py                # S3 asset -> EB ApplicationVersion — standalone bootstrap
          elastic_beanstalk_application.py   # tool only; NOT wired into routine deploys (see journal)
          elastic_beanstalk_environment.py   # creates one Environment only, never an Application
          web_app_instance_role.py
      # future: database/ lives here as its own sibling submodule, same shape as elastic_beanstalk/
    tests/
    app.py                             # always creates ApplicationStack once + one EnvironmentStack
    cdk.json
    requirements.txt
    requirements-dev.txt
  test-apps/                          # real apps used to exercise the deploy pipeline
    snack-recommender/
      app/
        __init__.py
        config.py
        extensions.py
        models.py
        seed.py
        routes/
          snacks.py
          users.py
          recommendations.py
      wsgi.py
      Procfile
      requirements.txt
      requirements-dev.txt
      README.md
  pipeline/                            # CI/CD — its own separate CDK project, sibling to infra/
    .venv/
    cdk.out/
    pipeline/                          # Python package (named after the "pipeline/" folder)
      __init__.py
      pipeline_stack.py                # app deploys: build once, promote dev->test->[approval]->
      resource_pipeline_stack.py       # stage->[approval]->prod (same shape, deploys infra/ stacks)
      config/
        __init__.py
        targets.py                     # TargetRef / TARGETS — one entry per (app, environment)
      constructs/
        __init__.py
        deploy_target.py               # DeployTarget Protocol — pipeline depends on this, not on EB
        elastic_beanstalk_deploy_target.py   # ElasticBeanstalkDeployAction, used by PipelineStack
        github_source_action.py        # Source action against an EXISTING, shared connection ARN —
        test_build_project.py          # the only way any pipeline touches GitHub; avoids
        cdk_deploy_project.py          # re-authorization. cdk_deploy_project.py runs `cdk deploy
                                        # <stack names> -c env=X` for ResourcePipelineStack
    app.py                             # GITHUB_BRANCH="main", one shared connection_arn for both stacks
    cdk.json
    requirements.txt
  docs/                                # this folder
    infra-overview.md
    pr-convention.md                   # title/description format, tied to .github/PULL_REQUEST_TEMPLATE.md
    elastic-beanstalk/                 # docs stay scoped by component, even though the code doesn't
      deploy-flow.md
      flow-diagram.svg                 # NOTE: still shows the old single-stack model, not yet updated
    snack-recommender/
      overview.md                      # data model + API reference (README covers setup instead)
    journal/                           # chronological, cross-cutting — not split by component
      README.md
      2026-09-14/
        01-iam-user-and-access-key-setup.md
        02-cdk-base-template-first-deploy.md
      2026-09-15/
        01-multi-stack-elastic-beanstalk-submodules.md
        02-snack-recommender-flask-app.md
        03-app-bundle-deploy.md
      2026-09-16/
        01-app-name-fix-and-shared-config.md
        02-pipeline-build.md
        03-pipeline-confirmed-working.md
        04-resource-pipeline-and-connection-fix.md
      2026-09-17/
        01-application-environment-separation.md
```

The CDK project itself is not named after Elastic Beanstalk — it's the general
infrastructure-as-code project for this app, and EB is just the first thing it provisions.
Future AWS resources (RDS, etc.) get their own submodule inside `infra/infra/` (same shape as
`elastic_beanstalk/`: its own `infra_stack.py`, `config/`, and `constructs/`), keeping each
resource independently deployable within the one CDK app. Their docs still get their own
subfolder under `docs/`, since documentation benefits from being scoped by topic even when the
underlying code doesn't split that way.

## Design principle: config vs. constructs vs. stack

Three distinct layers, kept deliberately separate:

- **`config/`** — pure data. Dataclasses with no AWS SDK calls and no CDK imports. Describes
  *what* should exist for a given environment (how many instances, what size, what IAM names),
  without knowing *how* to create it.
- **`constructs/`** — CDK logic. Each construct is responsible for provisioning one coherent
  piece of infrastructure, named after what it does (not the AWS service it happens to wrap).
- **`application_stack.py`** / **`environment_stack.py`** — composition only. Wire constructs
  together and pass config down. Neither should ever contain provisioning logic itself. Split
  into two files, not one, because an EB Application and an EB Environment have different
  deploy lifecycles (once, ever vs. once per environment) — see `elastic-beanstalk/deploy-flow.md`.

For how these layers actually work together to deploy an app to Elastic Beanstalk, see
**`elastic-beanstalk/deploy-flow.md`**.

## Known pinned values

- **`solution_stack_name`**: `"64bit Amazon Linux 2023 v4.13.8 running Python 3.13"` — verified
  against `aws elasticbeanstalk list-available-solution-stacks` directly, not guessed.
- **IAM managed policies**: `AWSElasticBeanstalkWebTier`, `AWSElasticBeanstalkMulticontainerDocker`
  — AWS-maintained, attached to a custom-created role rather than assumed to pre-exist.
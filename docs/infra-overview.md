# Infrastructure Overview

Directory structure, as of the first successful `cdk deploy`:

```
sentinel/                              # repo root
  infra/                               # CDK project — provisions EB now, more AWS resources later
    .venv/
    cdk.out/
    infra/                             # Python package (named after the "infra/" folder — CDK convention)
      __init__.py
      config/                          # shared across every resource submodule — not owned by one
        __init__.py
        environments.py                # canonical ENVIRONMENT_NAMES list
      elastic_beanstalk/               # one submodule per independently-deployable resource
        __init__.py
        infra_stack.py                 # Stack: composition root for this resource
        config/
          __init__.py
          scaling.py
          instance.py
          iam.py                       # suffixes only — app_name is passed in, not hardcoded
          environment.py
        constructs/
          __init__.py
          app_bundle.py                # S3 asset -> EB ApplicationVersion (bootstrap-only; see journal)
          web_app_hosting.py
          web_app_instance_role.py
      # future: database/ lives here as its own sibling submodule, same shape as elastic_beanstalk/
    tests/
    app.py                             # CDK entry point — app_name="snack-recommender"
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
      pipeline_stack.py                # Source (GitHub) -> Build (CodeBuild) -> Deploy (DeployTarget)
      config/
        __init__.py
        targets.py                     # TargetRef / TARGETS registry — the shared-config alternative
      constructs/                      # to a CDK cross-stack reference; see journal for why
        __init__.py
        deploy_target.py               # DeployTarget Protocol — pipeline depends on this, not on EB
        elastic_beanstalk_deploy_target.py
    app.py
    cdk.json
    requirements.txt
  docs/                                # this folder
    infra-overview.md
    elastic-beanstalk/                 # docs stay scoped by component, even though the code doesn't
      deploy-flow.md
      flow-diagram.svg
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
- **`infra_stack.py`** — composition only. Wires constructs together and passes config down. It
  should never contain provisioning logic itself.

For how these three layers actually work together to deploy an app to Elastic Beanstalk, see
**`elastic-beanstalk/deploy-flow.md`**.

## Known pinned values

- **`solution_stack_name`**: `"64bit Amazon Linux 2023 v4.13.8 running Python 3.13"` — verified
  against `aws elasticbeanstalk list-available-solution-stacks` directly, not guessed.
- **IAM managed policies**: `AWSElasticBeanstalkWebTier`, `AWSElasticBeanstalkMulticontainerDocker`
  — AWS-maintained, attached to a custom-created role rather than assumed to pre-exist.
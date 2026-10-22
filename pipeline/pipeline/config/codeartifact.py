# Matches infra/infra/codeartifact/codeartifact_stack.py's CodeArtifactStack constants.
# Duplicated by name rather than imported -- pipeline/ and infra/ are separate CDK apps/packages,
# same reasoning as ElasticBeanstalkDeployTarget targeting EB resources by name only.
CODEARTIFACT_DOMAIN = "sentinel-platform"
CODEARTIFACT_REPOSITORY = "platform-packages"

#!/bin/bash
# Primes pip with a CodeArtifact-backed index before EB's own `pip install -r requirements.txt`
# runs, so private packages (e.g. platform_core) resolve on a real deployed instance. Uses the
# instance role's own credentials (via IMDS) -- see infra/app.py for the granted permissions.
#
# Domain/repository are hardcoded, not read from EB's "Software: environment properties" --
# prebuild hooks run before EB materializes those into the shell environment, so a custom env var
# is simply unset at this phase (confirmed live: "CODEARTIFACT_DOMAIN: unbound variable"). These
# values are platform-wide constants anyway (infra/infra/codeartifact/codeartifact_stack.py), not
# real per-environment config, so hardcoding them here is the more honest shape, not a shortcut.
set -euo pipefail

CODEARTIFACT_DOMAIN="sentinel-platform"
CODEARTIFACT_REPOSITORY="platform-packages"

IMDS_TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
REGION=$(curl -s -H "X-aws-ec2-metadata-token: $IMDS_TOKEN" http://169.254.169.254/latest/meta-data/placement/region)
ACCOUNT=$(aws sts get-caller-identity --region "$REGION" --query Account --output text)

AUTH_TOKEN=$(aws codeartifact get-authorization-token \
    --domain "$CODEARTIFACT_DOMAIN" \
    --domain-owner "$ACCOUNT" \
    --region "$REGION" \
    --query authorizationToken --output text)

REPO_ENDPOINT=$(aws codeartifact get-repository-endpoint \
    --domain "$CODEARTIFACT_DOMAIN" \
    --domain-owner "$ACCOUNT" \
    --repository "$CODEARTIFACT_REPOSITORY" \
    --format pypi \
    --region "$REGION" \
    --query repositoryEndpoint --output text)

# /etc/pip.conf is a system-wide pip config, so it applies regardless of which staging venv the
# EB engine creates for this deploy -- the venv's own pip still reads it.
cat > /etc/pip.conf <<PIPCONF
[global]
extra-index-url = https://aws:${AUTH_TOKEN}@${REPO_ENDPOINT#https://}simple/
PIPCONF

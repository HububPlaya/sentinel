from opentelemetry.sdk.resources import Resource


def build_resource(*, app_id: str, team: str, environment: str) -> Resource:
    return Resource.create({"app_id": app_id, "team": team, "environment": environment})

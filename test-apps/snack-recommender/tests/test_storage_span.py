import json

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Snack
from platform_core.telemetry.context import start_span
from platform_core.telemetry.spans import instrument_call


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


def test_real_db_call_through_snack_recommenders_actual_connection_is_observed(capsys):
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        db.session.add(Snack(name="Pocky", country_of_origin="Japan", cuisine_type="snack"))
        db.session.commit()

        with start_span("db check"):
            result = instrument_call(
                resource="rds:snack-recommender-db",
                operation="select_snacks",
                call=lambda: Snack.query.all(),
            )

    assert len(result) == 1
    assert result[0].name == "Pocky"

    log_lines = [line for line in capsys.readouterr().out.strip().splitlines() if line]
    all_records = [json.loads(line) for line in log_lines]
    # filter by "severity" (unique to our own log schema), not "resource" --
    # OTel's own span JSON also has a top-level "resource" key (its Resource
    # attributes), so that would have matched both the log and the span dump.
    records = [record for record in all_records if "severity" in record]
    assert len(records) == 1
    record = records[0]
    assert record["resource"] == "rds:snack-recommender-db"
    assert record["operation"] == "select_snacks"
    assert record["outcome"] == "success"
    assert record["duration_ms"] > 0, "expected a real measured duration, not a stub"

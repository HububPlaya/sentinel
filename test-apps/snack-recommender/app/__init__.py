from flask import Flask, g

from platform_core.telemetry.context import configure, start_span
from platform_core.telemetry.logging import PlatformLogger

from .config import Config
from .extensions import db, migrate


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    configure(
        app_id=app.config["APP_ID"],
        team=app.config["TEAM"],
        environment=app.config["ENVIRONMENT"],
    )

    db.init_app(app)
    migrate.init_app(app, db)

    logger = PlatformLogger()

    @app.before_request
    def _start_request_span():
        g._telemetry_span_cm = start_span("request")
        g._telemetry_span_cm.__enter__()
        logger.info("request received")

    @app.teardown_request
    def _end_request_span(exc=None):
        span_cm = g.pop("_telemetry_span_cm", None)
        if span_cm is not None:
            exc_info = (type(exc), exc, exc.__traceback__) if exc else (None, None, None)
            span_cm.__exit__(*exc_info)

    with app.app_context():
        from . import models  # noqa: F401 -- ensures models are registered before migrations autogenerate
        from .routes.recommendations import recommendations_bp
        from .routes.snacks import snacks_bp
        from .routes.users import users_bp

        app.register_blueprint(snacks_bp)
        app.register_blueprint(users_bp)
        app.register_blueprint(recommendations_bp)

    @app.get("/health")
    def health():
        logger.info("health check completed")
        return {"status": "ok"}, 200

    @app.errorhandler(Exception)
    def _log_unhandled_exception(error):
        logger.error("unhandled exception", error_type=type(error).__name__)
        return {"error": "internal server error"}, 500

    @app.cli.command("seed-db")
    def seed_db_command():
        """Seeds the snacks table if empty. Separate, deliberate, one-time action --
        unlike schema creation/migration, this should never run automatically."""
        from .seed import seed

        seed()

    return app
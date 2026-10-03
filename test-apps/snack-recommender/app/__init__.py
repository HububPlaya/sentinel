import uuid

from flask import Flask

from platform_core.telemetry.context import bind_context
from platform_core.telemetry.logging import PlatformLogger

from .config import Config
from .extensions import db, migrate


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)

    logger = PlatformLogger()

    @app.before_request
    def _bind_telemetry_context():
        bind_context(
            trace_id=str(uuid.uuid4()),
            app_id=app.config["APP_ID"],
            team=app.config["TEAM"],
            environment=app.config["ENVIRONMENT"],
        )
        logger.info("request received")

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
from flask import Flask

from .config import Config
from .extensions import db, migrate


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)

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
        return {"status": "ok"}, 200

    @app.cli.command("seed-db")
    def seed_db_command():
        """Seeds the snacks table if empty. Separate, deliberate, one-time action --
        unlike schema creation/migration, this should never run automatically."""
        from .seed import seed

        seed()

    return app
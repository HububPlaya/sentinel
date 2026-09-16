from flask import Flask

from .config import Config
from .extensions import db


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)

    with app.app_context():
        from . import models  # noqa: F401 — ensures models are registered before create_all/migrations
        from .routes.recommendations import recommendations_bp
        from .routes.snacks import snacks_bp
        from .routes.users import users_bp

        app.register_blueprint(snacks_bp)
        app.register_blueprint(users_bp)
        app.register_blueprint(recommendations_bp)

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    @app.cli.command("init-db")
    def init_db_command():
        """Creates tables from the current models. Temporary — replace with Alembic migrations
        once the schema needs to evolve without dropping data (see the earlier decision that
        table schema belongs to the app, not the CDK infra code)."""
        db.create_all()
        print("Initialized the database.")

    @app.cli.command("seed-db")
    def seed_db_command():
        from .seed import seed

        seed()

    return app
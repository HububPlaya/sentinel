# Snack Recommender

A snack recommendation API with an emphasis on foreign/international snacks. This is the first
of the `test-apps/` — real, working code used to exercise the Elastic Beanstalk deploy pipeline
(`infra/`), not a toy chaos-endpoint app. No auth in v1; a "user" is just an email.

## Run locally

```
cd test-apps/snack-recommender
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements-dev.txt
copy .env.example .env      # then edit if needed — defaults work as-is
flask --app wsgi init-db
flask --app wsgi seed-db
flask --app wsgi run
```

Defaults to a local SQLite file — no AWS or Postgres needed to develop against this.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/users` | Create a user (`{"email": "..."}`) |
| GET | `/users/<id>` | Fetch a user |
| GET | `/snacks` | Browse/filter snacks (`?cuisine=`, `?country=`, `?flavor=`) |
| GET | `/snacks/<id>` | Fetch one snack |
| POST | `/snacks/<id>/rate` | Rate a snack (`{"user_id": 1, "rating": 5, "review_text": "..."}`) |
| GET | `/recommendations/<user_id>` | Recommended snacks based on rating history |

## What's deliberately not here yet

- Migrations (Alembic/Flask-Migrate) — using `flask init-db` (`db.create_all()`) for now.
  Table schema is owned by this app, not by the CDK infra code — see
  `docs/elastic-beanstalk/deploy-flow.md` for that reasoning.
- Real Postgres/RDS wiring — `DATABASE_URL` just needs to point at one once it exists.
- Deployment onto Elastic Beanstalk itself — this app is what the upcoming CI/CD work
  (S3 bundle → `CfnApplicationVersion` → `version_label`) will actually deploy.
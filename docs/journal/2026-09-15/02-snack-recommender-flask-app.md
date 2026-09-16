---
date: 2026-09-15
sequence: 02
commit: bcf1569
---

# Built the snack-recommender Flask app (test-apps/)

- Built the first app under `test-apps/` — a snack recommendation API with an emphasis on
  foreign/international cuisine. This is the real, working app the upcoming EB bundle-deploy
  and CI/CD work will actually deploy, not a placeholder or chaos-endpoint stand-in.
- Real relational schema: `snacks`, `users`, `ratings`, with actual foreign keys — chosen
  deliberately because the recommendation logic needs joins (cuisines a user rated highly →
  other snacks from those cuisines they haven't tried), which is exactly what motivated using
  RDS/Postgres over DynamoDB earlier.
- No auth in v1 — a user is just an email, created up front and referenced by id. Deliberate
  scope cut to focus on the recommendation logic and infra first.
- Config reads `DATABASE_URL` from the environment, defaulting to local SQLite — the app runs
  and is fully testable with zero AWS/Postgres involvement before it ever touches EB.
- Seeded a starter dataset of 15 real international snacks across cuisines (Japanese, Georgian,
  Filipino, Turkish, Vietnamese, etc.) via a `flask seed-db` CLI command.
- Table creation currently uses `db.create_all()` via a `flask init-db` command — a deliberate
  placeholder. Real migrations (Alembic/Flask-Migrate) are still deferred, consistent with the
  earlier decision that schema is owned by the app, not the CDK infra code.
- Hit a real dependency issue on first `pip install`: `psycopg2-binary==2.9.9` tried to build
  from source and failed with `pg_config executable not found`. Root cause: that pinned version
  doesn't ship a prebuilt wheel for Python 3.13 — Python 3.13 wheel support was only added in
  `psycopg2-binary` 2.9.10. Fixed by bumping the pinned version in `requirements.txt`.
- Confirmed the full local loop works: `flask init-db` created tables, `flask seed-db` loaded
  the 15 starter snacks, `flask run` served the app, and `GET /snacks` returned the seeded data
  in the browser at `127.0.0.1:5000/snacks`.
- VS Code showed a notice that `.env` values weren't being injected into the integrated
  terminal (a VS Code setting, `python.terminal.useEnvFile`, not an app bug). Didn't matter yet
  since SQLite fallback defaults covered it, but fixed properly for when `DATABASE_URL` needs
  to point at real Postgres later — added `load_dotenv()` to `wsgi.py` so the app loads `.env`
  itself, independent of any terminal/editor setting.

## Next up (not yet started)

- Wire up the actual bundle-deploy mechanism onto Elastic Beanstalk: S3 asset,
  `CfnApplicationVersion`, and setting `version_label` on the environment — this is what
  replaces EB's default sample app with this real one.
- RDS/Postgres, so `DATABASE_URL` points at something real instead of SQLite once deployed.
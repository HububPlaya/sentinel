# Snack Recommender — overview

Reference for the data model and API. For setup/run instructions, see
`test-apps/snack-recommender/README.md` — this doc covers *what it is*, not *how to run it*.

## Why this app exists

This is the real application the Elastic Beanstalk infrastructure (`infra/`) deploys. It
exists so the deploy pipeline, and later the HTTPS/CI-CD work, has something genuine to exercise
instead of EB's default sample app.

## Data model

Three tables, with real foreign-key relationships — chosen deliberately because the
recommendation logic needs relational joins, not just key-value lookups:

```
users
  id, email, created_at

snacks
  id, name, country_of_origin, cuisine_type, description, flavor_tags, image_url

ratings
  id, user_id (FK -> users), snack_id (FK -> snacks), rating (1-5), review_text, created_at
  unique constraint on (user_id, snack_id) — one rating per user per snack
```

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/users` | Create a user — `{"email": "..."}`, no auth in v1 |
| GET | `/users/<id>` | Fetch a user |
| GET | `/snacks` | Browse/filter — `?cuisine=`, `?country=`, `?flavor=` |
| GET | `/snacks/<id>` | Fetch one snack, with average rating |
| POST | `/snacks/<id>/rate` | Rate a snack — `{"user_id", "rating", "review_text"}`; re-rating updates rather than duplicates |
| GET | `/recommendations/<user_id>` | See below |

## Recommendation logic (v1)

Deliberately simple — real SQL joins, not ML:

1. Find cuisines the user has rated 4 or higher.
2. Suggest other snacks from those cuisines they haven't rated yet, ranked by average rating.
3. If they have no rating history, fall back to the highest-rated snacks overall.

## What's intentionally not here yet

- **Migrations** — schema is currently created via `db.create_all()` (`flask init-db`), not
  Alembic/Flask-Migrate. Schema is owned by this app, not by the CDK infra code — see
  `docs/elastic-beanstalk/deploy-flow.md` for why that split matters.
- **Real Postgres** — `DATABASE_URL` defaults to local SQLite; point it at a real RDS instance
  once one exists.
- **Auth** — a user is just an email for now.
- **Deployment onto EB** — this app isn't wired into the CDK stack yet. That's the next piece:
  an S3 bucket, a `CfnApplicationVersion`, and setting `version_label` on the environment.
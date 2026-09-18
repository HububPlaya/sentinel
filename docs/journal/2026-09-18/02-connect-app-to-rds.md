---
date: 2026-09-18
sequence: 02
commit: 30b6b3e
---

# Connected snack-recommender to RDS via Secrets Manager

## Real gap found while reviewing the app before wiring in the database

`wsgi.py` never actually called `load_dotenv()`, despite `python-dotenv` being a listed
dependency and `.env`/`.env.example` existing in the project. `.env` loading had never worked —
a pre-existing, unrelated gap, fixed alongside this work since it directly affects whether local
testing of the new config actually behaves as documented. `.env.example` itself was also
completely empty; given real content documenting the (all-optional) local variables.

## Split config.py into declaration vs. AWS-specific fetching

New `app/aws_secrets.py` — isolates the Secrets Manager fetch and the AWS-vs-local branching
(`is_running_on_aws()`, `get_database_url()`, `get_database_read_url()`) from `config.py`, which
now just declares what Flask needs. Same separation already used throughout `infra/`
(`config/` vs. the constructs that produce values), applied here for the same reason: `config.py`
staying a plain declaration makes it obvious at a glance what Flask actually needs, without the
AWS-specific mechanics in the way.

`DATABASE_READ_URL` is exposed but not used anywhere yet — the app has no code today that
distinguishes read vs. write queries. Deliberately left unimplemented rather than building
routing logic before there's an actual reason to use it.

## Retry configured explicitly on the Secrets Manager client

Given today's earlier EB security-group bug turned out to hinge on a startup-adjacent timing
gap, added explicit retry config (`mode="standard"`, `max_attempts=5`) to the `boto3` client
rather than trusting bare defaults — a freshly-launched EC2 instance's IAM credentials can have a
brief propagation window right after boot, the same category of "just became available, not
everywhere yet" issue. Cheap insurance against a class of bug already proven real today.

## infra/app.py: added AWS_REGION

`boto3` generally auto-detects its region via EC2 instance metadata without needing this set
explicitly — so this isn't a hard requirement, more a continuation of today's broader theme
(explicit over implicit, given how many implicit-default bugs surfaced earlier). One line added
to `app_environment_variables`.

## Confirmed: local testing can only validate part of this

RDS's security group only allows inbound traffic from the EB security group — a local machine
was never going to be able to reach it, by design, the same isolation the whole access model was
built around. Local testing can confirm the app boots and the SQLite fallback path works
(`is_running_on_aws()` correctly evaluates `False` with no `DB_SECRET_ARN` set); it cannot
confirm the real Postgres connection. Ran `flask --app wsgi run` locally after fixing a `flask`
command not found error — turned out to be the `infra/` virtualenv still active instead of a
`snack-recommender`-specific one; installing into the wrong venv entirely, not a real app bug.
`/health` confirmed `200 OK` locally.

## Next up (not yet started)

- Commit and merge to `main` — the real test (actual RDS connectivity) can only happen once both
  the resource pipeline (for `AWS_REGION`) and the app pipeline (for the new code) have deployed.
- `db.create_all()` has still never run against the real RDS instance — `/snacks` will likely
  still fail or return empty even once the connection itself works, until this is resolved.
  Decision still open: a one-off manual command, or wired into app startup (safe, since
  `create_all()` is idempotent, unlike `seed()` which already guards against duplicate seeding).

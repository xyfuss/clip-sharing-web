# XYFUSS

A small Flask web app for uploading and sharing gameplay clips, live at [xyfuss.com](https://xyfuss.com).

I built it to learn web development end to end: backend, database, cloud storage, security, testing and deployment. Registration is closed on the live site, but you can run your own copy locally (see [Getting started](#getting-started)).

<!-- Add a screenshot of the clips page here: ![ClipVault clips page](docs/screenshot.png) -->

## Features

- Sign up and log in with hashed passwords (bcrypt).
- Upload clips (mp4, webm, mov or mkv, up to 50 MB) with a title and game. Files go **straight from the browser to Cloudflare R2**, and the upload button fills up as it progresses.
- Browse a grid of clips and play them in the page.
- Delete your own clips. The database row and the stored video are both removed.
- Nightly PostgreSQL backups to a private bucket, with a tested restore procedure.
- Automated tests and dependency checks on every pull request.

## Tech stack

| Area              | Tools                                                     |
| ----------------- | --------------------------------------------------------- |
| Backend           | Python 3.13, Flask, Flask-Login, Flask-WTF, Flask-Limiter |
| Database          | PostgreSQL on Neon, SQLAlchemy, Flask-Migrate             |
| File storage      | Cloudflare R2 (S3-compatible) via boto3                   |
| Hosting           | Render, served with gunicorn                              |
| CI and automation | GitHub Actions (tests, dependency audit, nightly backups) |
| Tests             | pytest                                                    |

## How uploads work

Videos never pass through the Flask server, so the web server stays small and uploads don't depend on its bandwidth.

1. The browser sends the file's type and size to `POST /upload/sign`. The server checks them against an allowlist and a size limit, picks a random UUID file name, and returns a short-lived **presigned PUT URL**.
2. The browser uploads the file directly to R2 with `XMLHttpRequest`, which gives progress events for the button animation.
3. The browser calls `POST /upload/complete`. The server confirms the object exists, re-checks its real size with `head_object`, rejects duplicates, and creates the database row.

Deleting a clip removes the database row first and then the R2 object, so a failed storage delete can only leave an unseen orphan file and never a broken clip on the page.

## Security

- Passwords are hashed with bcrypt, with length limits on both registration and login.
- Session cookies are `Secure`, `HttpOnly` and `SameSite=Lax`.
- CSRF protection (Flask-WTF) on every form and `fetch` request.
- Rate limiting (Flask-Limiter) on login, registration and upload signing, with `ProxyFix` so limits apply per real client IP behind Render's proxies.
- Uploads are validated by content type and size on the server, not just in the browser. File names are random and never taken from user input.
- Secrets live in environment variables. `.env` is git-ignored, and CI never uses production credentials.

## Getting started

### Prerequisites

- Python 3.13
- A PostgreSQL database (a free Neon project works), or leave `DATABASE_URL` unset to use local SQLite
- A Cloudflare R2 bucket with an API token (Object Read & Write) and a CORS rule that allows `PUT` from your local origin

### Setup

```bash
git clone <your-fork-or-this-repo>
cd webapp
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # or create .env by hand (see below)
flask db upgrade
flask run
```

Then open http://127.0.0.1:5000.

### Environment variables

Create a `.env` file in the project root. Never commit it.

| Variable                                    | Purpose                                                                                                       |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `SECRET_KEY`                                | Signs sessions and CSRF tokens. Use a long random value.                                                      |
| `DATABASE_URL`                              | PostgreSQL connection string. Defaults to local SQLite if unset.                                              |
| `R2_ENDPOINT_URL`                           | Your R2 S3 endpoint (`https://<account-id>.r2.cloudflarestorage.com`).                                        |
| `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | R2 API token credentials.                                                                                     |
| `R2_BUCKET_NAME`                            | Bucket that stores the clips.                                                                                 |
| `R2_PUBLIC_URL`                             | Public base URL used to play clips.                                                                           |
| `REGISTRATION_ENABLED`                      | Set to `false` to close sign-ups (the live site does this). Defaults to `true`.                               |
| `SESSION_COOKIE_SECURE`                     | Defaults to `true`. Set to `false` in your local `.env` only, because local development runs over plain HTTP. |

### Run the tests

```bash
pip install -r requirements-dev.txt
pytest -v
```

The tests set their own environment before importing the app and use an in-memory SQLite database, so they never touch real services.

## Project structure

```text
webapp/
├── .github/               # GitHub configuration
│   └── workflows/         # GitHub Actions pipelines
│       ├── backup.yml     # Nightly pg_dump to a private R2 bucket
│       └── ci.yml         # Tests and dependency audit on push and pull requests
├── migrations/            # Flask-Migrate / Alembic database migrations
│   ├── versions/          # Migration scripts (initial schema)
│   ├── alembic.ini
│   ├── env.py
│   └── script.py.mako
├── static/
│   └── style.css          # Site styling
├── templates/             # Jinja templates
│   ├── base.html          # Shared layout and CSRF meta tag
│   ├── clips.html         # Clip grid with delete buttons
│   ├── home.html          # Page shown after login
│   ├── login.html
│   ├── register.html
│   └── upload.html        # Upload form, progress button, direct-to-R2 script
├── tests/                 # Automated tests
│   ├── conftest.py        # Isolated test app (SQLite, fake environment)
│   └── test_auth.py       # Login and registration tests
├── .env.example           # Template for local environment variables
├── .gitignore             # Files Git should ignore (.env, venv, ...)
├── Procfile               # gunicorn start command for Render
├── README.md              # Project description, setup and documentation
├── app.py                 # Flask app: models, routes and security setup
├── neon.ts                # Neon CLI config (not needed to run the app)
├── package.json           # Neon CLI tooling only (with package-lock.json)
├── pytest.ini             # pytest settings
├── requirements-dev.txt   # Adds pytest for development and CI
└── requirements.txt       # Pinned runtime dependencies
```

## Deployment and operations

- **Hosting:** Render runs `gunicorn app:app` (see `Procfile`). Configuration, including the database URL and R2 credentials, is set as Render environment variables.
- **Migrations:** run `flask db upgrade` against the target database after schema changes.
- **CI:** `.github/workflows/ci.yml` runs the tests and `pip-audit` on pushes to `main` and on pull requests.
- **Backups:** `.github/workflows/backup.yml` runs `pg_dump` every night and uploads the dump to a private R2 bucket. The credentials are stored as GitHub Actions secrets. To restore, create a scratch database or Neon branch and run:

  ```bash
  pg_restore --clean --if-exists --no-owner --no-privileges -d "<scratch connection string>" backup-YYYY-MM-DD.dump
  ```

  Always restore into a scratch target first and check the row counts. Never restore over the live database.

## Roadmap

- Security headers and a Content-Security-Policy.
- More tests (CSRF, rate limiting, the sign and complete routes with a fake S3 client).
- Background thumbnail generation.

## What I learned

- Why presigned URLs, CORS and server-side validation matter for direct-to-storage uploads.
- How CSRF tokens, cookie flags and rate limiting work, including the proxy problem behind rate limits.
- How to set up automated tests, CI, dependency auditing and verified backups.

# Chess Behavioral Analytics Platform (Flask MVP)

Flask MVP for behavioral chess analytics using Lichess data.  
The app focuses on player behavior patterns (tilt, time management, weaknesses, opening outcomes) instead of deep engine analysis.

## Highlights

- Lichess OAuth2 account connection
- Recent game import from Lichess API
- Local game storage (SQLite/PostgreSQL via SQLAlchemy)
- Behavioral analytics modules:
  - Tilt detection
  - Opening performance
  - Time management (real clock parsing + simulation fallback)
  - Weakness heuristics
- Dashboard + analytics pages with TailwindCSS and Chart.js
- Flask Blueprint architecture
- Docker-ready and deployable to Railway/Render

## Tech Stack

- Python 3.12+
- Flask, Flask-Login, Flask-SQLAlchemy
- pandas, numpy, python-chess
- PostgreSQL support (`psycopg2-binary`)
- TailwindCSS (CDN), Chart.js (CDN)
- Docker / docker-compose

## Project Structure

```text
app/
  __init__.py
  config.py
  extensions.py
  auth/
    __init__.py
    routes.py
  dashboard/
    __init__.py
    routes.py
  analytics/
    __init__.py
    routes.py
    openings.py
    tilt.py
    time_management.py
    weaknesses.py
    reports.py
  lichess/
    __init__.py
    client.py
    routes.py
    service.py
  models/
    __init__.py
    user.py
    game.py
    analysis_report.py
  templates/
    base.html
    partials/flash.html
    auth/login.html
    dashboard/index.html
    analytics/index.html
    analytics/openings.html
    analytics/weaknesses.html
  static/
    css/app.css
instance/
requirements.txt
run.py
Dockerfile
docker-compose.yml
.env.example
README.md
```

## Environment Variables

Copy `.env.example` to `.env` and fill values:

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Flask session signing key. Use a strong random value in production. |
| `LICHESS_CLIENT_ID` | Yes | Self-chosen unique app string (no registration needed), e.g. `my-chess-app`. |
| `LICHESS_OAUTH_AUTHORIZE_URL` | No | OAuth authorize endpoint. Default: `https://lichess.org/oauth`. |
| `LICHESS_OAUTH_TOKEN_URL` | No | OAuth token endpoint. Default: `https://lichess.org/api/token`. |
| `LICHESS_API_BASE` | No | Lichess API base URL. Default: `https://lichess.org/api`. |
| `DATABASE_URL` | Yes | `sqlite:///...` for local or PostgreSQL URL for production. |
| `FLASK_ENV` | No | Flask environment (`development` / `production`). |
| `SESSION_COOKIE_SECURE` | No | Set `1` behind HTTPS in production. |
| `REMEMBER_COOKIE_SECURE` | No | Set `1` behind HTTPS in production. |
| `REDIS_URL` | No | Placeholder for future background jobs/caching. |
| `ENABLE_BACKGROUND_JOBS` | No | Placeholder flag (`0` or `1`). |

## Local Setup (Without Docker)

1. Create and activate virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy env file:
   ```bash
   cp .env.example .env
   ```
4. Set your `LICHESS_CLIENT_ID` in `.env` (self-chosen value, no client secret).
5. Run app:
   ```bash
   python run.py
   ```
6. Open `http://localhost:5000`.

## Docker Setup

1. Create `.env` from `.env.example`.
2. Build and start services:
   ```bash
   docker compose up --build
   ```
3. Open `http://localhost:5000`.

Notes:
- `web` starts Flask dev server by default in compose.
- `db` starts PostgreSQL at `localhost:5432`.
- For SQLite-only local usage, set `DATABASE_URL=sqlite:///chess_behavioral.db`.

## Lichess OAuth Flow

1. User opens login page.
2. Clicks **Connect Lichess**.
3. App generates PKCE values (`code_verifier`, `code_challenge`) and redirects to Lichess OAuth consent.
4. Lichess redirects back to `/auth/callback` with authorization code.
5. App exchanges code + PKCE verifier for an access token and stores linked user.

## Behavioral Analytics Included

- **Tilt Detection**
  - Losing streaks
  - Rapid requeue after losses
  - Accuracy drop placeholder metric
  - Result level: `LOW`, `MEDIUM`, `HIGH`

- **Opening Analysis**
  - Most played openings
  - Best winrate openings
  - Worst openings

- **Time Management**
  - Average move time
  - Fast move ratio
  - Panic move ratio
  - Uses PGN clock comments (`[%clk ...]`) when available
  - Falls back to simulation architecture when unavailable

- **Weakness Detection**
  - Endgame-heavy losses
  - Middlegame stability losses (heuristic)
  - Poor results vs gambit openings

## Deployment (Railway / Render)

### Railway

1. Create project and connect repository.
2. Add environment variables from `.env.example`.
3. Set `DATABASE_URL` to Railway Postgres connection string.
4. Deploy with default `Dockerfile` or Python service.

### Render

1. Create a new Web Service from repository.
2. Runtime: Python 3.12+.
3. Build command:
   ```bash
   pip install -r requirements.txt
   ```
4. Start command:
   ```bash
   gunicorn --bind 0.0.0.0:$PORT run:app
   ```
5. Add environment variables and managed PostgreSQL.

## Extensibility Notes

This MVP is intentionally modular to support future upgrades:

- Background job queue (`REDIS_URL` placeholder, `ENABLE_BACKGROUND_JOBS`)
- Deeper analysis workers (Stockfish modules)
- ML-based prediction modules
- Telegram bot integration
- Realtime event ingestion
- API-first architecture

## Security Notes

- Secrets are environment-based (no hardcoded credentials).
- Use a strong `SECRET_KEY` in production.
- Set `SESSION_COOKIE_SECURE=1` and `REMEMBER_COOKIE_SECURE=1` behind HTTPS.

## Limitations (Current MVP)

- No full migration system yet (`db.create_all()` is used for MVP bootstrap).
- No deep engine/Stockfish analysis by design.
- Time analysis depends on PGN clock availability for high fidelity.

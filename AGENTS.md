# Game Tracker — Agent Instructions

## Stack
FastAPI, SQLAlchemy, SQLite, JWT auth, pytest, requests (RAWG/IGDB integration)

## Project layout (per spec)
```
app/
  __init__.py   # app factory
  models.py     # SQLAlchemy models: User, Game, Achievement
  routes.py     # API endpoints
  auth.py       # JWT registration/login
  external_api.py  # RAWG/IGDB integration
  achievements.py
  utils.py
tests/
  test_auth.py
  test_games.py
  test_achievements.py
requirements.txt
config.py
run.py
```

## Key design decisions
- Time stored in **minutes** (`play_time_minutes`), converted to hours on response
- Tags stored as **comma-separated string** (not a many-to-many table)
- Games paginated at **10 per page**
- Ratings: **1–10** integer scale
- SQLite via SQLAlchemy ORM

## API endpoints
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/register`, `/login` | Auth |
| GET/POST/PUT/DELETE | `/games` | CRUD collection |
| GET | `/games/{id}` | Detail |
| PATCH | `/games/{id}/playtime` | Add minutes |
| POST | `/games/{id}/achievements` | Add achievement |
| PUT | `/achievements/{id}` | Update achievement |
| GET | `/stats` | Aggregate stats |
| GET | `/search` | Search/filter games |

## Setup
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

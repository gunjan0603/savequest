# SaveQuest

> Save money. Score progress. Build a habit.

SaveQuest is a hackathon MVP that turns saving money into a positive game. Users create savings goals, manually log savings, earn points for the amount they save and consistency, and compare points with friends.

## Stack

- Python + Flask
- Flask-Login + Werkzeug password hashing
- Flask-SQLAlchemy + SQLite
- HTML + CSS + Jinja2
- Vanilla JavaScript (`fetch`) for instant savings feedback
- pytest

## Quick start

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python database/seed.py
python app.py
```

Open the local Flask URL shown in the terminal.

### Demo accounts

All seeded demo users use password `demo123`:

- aanya@example.com
- rohan@example.com
- priya@example.com

## Core flow

Sign up / log in → create goal → log savings → earn points → progress updates → leaderboard updates.

## API

Base URL: `/api`

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/goals`
- `POST /api/goals`
- `GET /api/goals/<goal_id>`
- `POST /api/goals/<goal_id>/savings`
- `GET /api/points`
- `GET /api/leaderboard`

## Tests

```bash
pytest -q
```

## Points rule used by this prototype

- 10 points per completed ₹100 saved.
- +25 consistency bonus when a savings entry continues a consecutive weekly saving pattern.

This is the simple fixed formula selected for the hackathon prototype from the PRD's example scoring direction.

## Project structure

```text
savequest/
├── app.py
├── config.py
├── models.py
├── points_logic.py
├── routes/api.py
├── templates/
├── static/
├── database/
├── tests/
└── README.md
```

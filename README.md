# E-DIM Copilot

AI Copilot for residential buildings (OSBB) that integrates with Telegram and personalises responses using internal building and apartment data.

## Features

- **Resident identity** — each user registers their name, apartment number and building address.
- **Building context** — the AI sees the latest announcements for the resident's building.
- **AI chat** — free-form questions answered by OpenAI with full building/apartment context.
- **Telegram commands**:
  | Command | Description |
  |---------|-------------|
  | `/start` | Welcome message |
  | `/register` | Multi-step onboarding (name → apartment → building address) |
  | `/myinfo` | Show stored profile |
  | `/events` | Show latest building announcements |
  | (any text) | AI-powered chat |

## Project Structure

```
edim/
├── edim/
│   ├── __init__.py
│   ├── config.py       # Config via env vars
│   ├── models.py       # SQLAlchemy models (Building, Resident, Announcement)
│   ├── storage.py      # CRUD helpers
│   ├── assistant.py    # Context builder + OpenAI call
│   ├── handlers.py     # Telegram command & message handlers
│   └── main.py         # Bot entry point
├── tests/
│   ├── test_storage.py
│   ├── test_assistant.py
│   └── test_handlers.py
├── requirements.txt
├── requirements-dev.txt
├── .env.example
└── pytest.ini
```

## Quick Start

```bash
# 1. Clone and install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env — set TELEGRAM_BOT_TOKEN and OPENAI_API_KEY

# 3. Run
python -m edim.main
```

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | — | Token from @BotFather |
| `OPENAI_API_KEY` | ✅ | — | OpenAI API key |
| `DATABASE_URL` | ❌ | `sqlite:///edim.db` | SQLAlchemy DB URL |
| `OPENAI_MODEL` | ❌ | `gpt-4o-mini` | OpenAI model name |

## Development

```bash
pip install -r requirements-dev.txt
pytest
```


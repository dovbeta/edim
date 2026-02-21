# E‑DIM Copilot

AI Copilot for residential buildings (OSBB) that integrates with messengers (Telegram/Viber) and personalizes responses using internal building and apartment data.

---

# 🏢 Overview

E‑DIM Copilot is an AI assistant for residents of apartment buildings that:

* answers questions about the building
* knows the user and their apartment
* integrates with Telegram
* uses internal OSBB data (debts, announcements, docs)

Example:

> **User:** When will water be restored?
> **Copilot:** Water supply in entrance 2 (your entrance) will be restored at 14:00.

---

# 🧠 Architecture

## Components

* **Telegram Bot** — user interface
* **API (FastAPI)** — chat endpoint & orchestration
* **Chat Gateway** — identity & linking logic
* **Orchestrator** — builds Copilot response
* **Context Manager** — loads user/building data
* **Integrations Runner** — imports data from external Providers
* **LLM Client** — AI model integration (planned)

## Data Stores

* **Postgres** — users, identities, units, buildings, organizations, providers
* **MongoDB** — documents & FAQ
* **Qdrant** — vector search
* **Redis** — cache/session (planned)

---

# 📂 Project Structure

```
EDim/

services/
  api/
    app/
      main.py
      orchestrator.py
      context_manager.py
      llm_client.py
      core/
      db/
        models/
      gateway/
      integrations/
        importers/
        sources/
        cli/

  telegram-bot/
    bot.py
    requirements.txt

docker-compose.yml

README.md
```

---

# 🚀 Quick Start (Podman)

## 1️⃣ Start Podman machine

```
podman machine start
```

## 2️⃣ Build & run

```
podman compose up --build
```

API will be available at:

```
http://localhost:8000
```

---

# 🤖 Telegram Bot

Environment variables:

```
TELEGRAM_TOKEN=xxxx
COPILOT_API_URL=http://api:8000
```

Bot flow:

1. User sends message
2. Copilot asks for phone (if not linked)
3. User shares contact
4. Identity linked to resident
5. Personalized Copilot responses

---

# 👤 Identity Model

```
provider → organization → building → unit ← user ← chat_identity
```

Tables:

* providers
* organizations
* buildings
* units (apartments, storages, etc.)
* users
* chat_identities
* user_units (m2m linking)

---

# 🔗 API Endpoints

## POST /chat

Text message from messenger

Request:

```
{
  "channel": "telegram",
  "external_user_id": "123",
  "message": "Hello",
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe"
}
```

Response:

```
{
  "text": "Copilot answer"
}
```

or

```
{
  "need_phone": true,
  "text": "Share your phone"
}
```

---

## POST /chat/contact

Phone linking

Request:

```
{
  "channel": "telegram",
  "external_user_id": "123",
  "phone": "+380...",
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe"
}
```

---

# 🧪 Development

API auto‑reload enabled via:

```
uvicorn --reload
```

Telegram bot auto‑reload via:

```
watchmedo auto-restart
```

Importing data from provider:

```
python services/api/app/integrations/cli/import_provider.py --provider-id <id>
```

Selective import:

```
python services/api/app/integrations/cli/import_provider.py --provider-id <id> --include buildings --include units
```

Available options for `--include`: `buildings`, `units`, `residents`, `accruals`.

---

# 🗺 Roadmap

* ✅ Unit linking (formerly Apartment)
* ✅ Resident registry import (Providers framework)
* Context personalization
* LLM integration
* Resident Copilot MVP

---

# 🏗 Tech Stack

* FastAPI
* SQLAlchemy
* Postgres
* MongoDB
* Qdrant
* Telegram Bot API
* Podman / Docker

---

# 📜 License

Private project — E‑DIM

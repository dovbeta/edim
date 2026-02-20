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
* **LLM Client** — AI model integration (planned)

## Data Stores

* **Postgres** — users, identities, apartments
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
      core/
      db/
      gateway/
      orchestrator/
      llm/

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
2. Copilot asks for phone
3. User shares contact
4. Identity linked to resident
5. Personalized Copilot responses

---

# 👤 Identity Model

```
chat_identity → phone → user → apartment
```

Tables:

* users
* chat_identities
* apartments
* buildings
* user_apartments

---

# 🔗 API Endpoints

## POST /chat

Text message from messenger

Request:

```
{
  "channel": "telegram",
  "external_user_id": "123",
  "message": "Hello"
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

```
{
  "channel": "telegram",
  "external_user_id": "123",
  "phone": "+380..."
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

---

# 🗺 Roadmap

* Apartment linking
* Resident registry import
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

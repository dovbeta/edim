# EвЂ‘DIM Copilot

AI Copilot for residential buildings (OSBB) that integrates with messengers (Telegram/Viber) and personalizes responses using internal building and unit data.

---

# рџЏў Overview

EвЂ‘DIM Copilot is an AI assistant for residents of apartment buildings that:

* answers questions about the building
* knows the user and their unit
* integrates with Telegram
* uses internal OSBB data (debts, announcements, docs)

Example:

> **User:** When will water be restored?
> **Copilot:** Water supply in entrance 2 (your entrance) will be restored at 14:00.

---

# рџ§  Architecture

## Components

* **Telegram Bot** вЂ” user interface
* **API (FastAPI)** вЂ” chat endpoint & orchestration
* **Chat Gateway** вЂ” identity & linking logic
* **Orchestrator** вЂ” builds Copilot response
* **Context Manager** вЂ” loads user/building data
* **LLM Client** вЂ” AI model integration (planned)

## Data Stores

* **Postgres** вЂ” users, identities, units
* **MongoDB** вЂ” documents & FAQ
* **Qdrant** вЂ” vector search
* **Redis** вЂ” cache/session (planned)

---

# рџ“‚ Project Structure

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

# рџљЂ Quick Start (Podman)

## 1пёЏвѓЈ Start Podman machine

```
podman machine start
```

## 2пёЏвѓЈ Build & run

```
podman compose up --build
```

API will be available at:

```
http://localhost:8000
```

---

# рџ¤– Telegram Bot

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

# рџ‘¤ Identity Model

```
chat_identity в†’ phone в†’ user в†’ unit
```

Tables:

* users
* chat_identities
* units
* buildings
* user_units

---

# рџ”— API Endpoints

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

# рџ§Є Development

API autoвЂ‘reload enabled via:

```
uvicorn --reload
```

Telegram bot autoвЂ‘reload via:

```
watchmedo auto-restart
```

---

# рџ—є Roadmap

* Unit linking
* Resident registry import
* Context personalization
* LLM integration
* Resident Copilot MVP

---

# рџЏ— Tech Stack

* FastAPI
* SQLAlchemy
* Postgres
* MongoDB
* Qdrant
* Telegram Bot API
* Podman / Docker

---

# рџ“њ License

Private project вЂ” EвЂ‘DIM


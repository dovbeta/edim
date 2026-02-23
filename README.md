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
* **Orchestrator** — handles the main chat pipeline
* **Context Manager** — loads user/building data
* **Planner** — LLM-based agent that decides on intent and SQL generation
* **SQL Validator & Executor** — ensures safe execution of generated queries
* **Responder** — LLM-based agent that formats the final answer
* **Integrations Runner** — imports data from external Providers
* **LLM Client** — Gemini integration (Google AI)

## Data Stores

* **Postgres** — structured data (users, units, buildings, organizations, vehicles)
* **MongoDB** — chat history, messages, and planner logs
* **Qdrant** — vector search (for RAG/documents - planned/integration in progress)
* **Redis** — cache/session (planned)

---

# 📂 Project Structure

```
EDim/
services/
  api/
    app/
      main.py
      orchestrator/
      planning/
      execution/
      response/
      context/
      llm/
      db/
        models/
      gateway/
      integrations/
        importers/
        sources/
        cli/
  telegram-bot/
    bot.py
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

# 🤖 AI Logic (Planning & Execution)

The Copilot uses a two-step approach for handling user queries:

1. **Planner:** The LLM receives the user's message, conversation history, and the database schema. It decides if the request needs data from the database. If so, it generates a safe, parameterized SQL query.
2. **Executor & Responder:** The SQL query is validated against a whitelist of tables and then executed. The resulting data is passed back to the LLM (Responder), which crafts a human-friendly response based on the actual data found.

This ensures the AI doesn't hallucinate data and strictly follows building-level access policies.

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
* vehicles (linked to user)
* user_organizations

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

Available options for `--include`: `buildings`, `units`, `residents`, `debts`.

---

# 🗺 Roadmap

* ✅ Unit linking (formerly Apartment)
* ✅ Resident registry import (Providers framework)
* ✅ LLM integration (Gemini)
* ✅ SQL-based planning and execution
* ✅ Chat history storage (MongoDB)
* 🚧 Resident Copilot MVP (in progress)
* 🚧 Context personalization (improving)
* 📅 Documents search (RAG)
* 📅 Multi-language support

---

# 🏗 Tech Stack

* **Backend:** FastAPI, SQLAlchemy (Async)
* **Database:** Postgres (Data), MongoDB (History/Logs)
* **LLM:** Google Gemini API
* **Deployment:** Docker / Podman
* **Bot:** Aiogram (Telegram)

---

# 📜 License

Private project — E‑DIM

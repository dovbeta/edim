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

# 📋 Requirements

## Functional Requirements

- **User Authentication & Identity Linking:** 
  - Automated identification of users via Telegram/Viber.
  - Linking user accounts to specific residential units using phone numbers.
  - Requesting contact information if the user is not recognized.
- **AI-Powered Chat Assistant:**
  - Natural language processing for user queries about building services, debts, and announcements.
  - Intelligent planning of data retrieval using LLM-generated SQL queries.
  - Context-aware responses that consider user's building, unit, and history.
- **Data Integration:**
  - Automated importing of building, unit, resident, and debt data from external providers (e.g., DAH).
  - Support for local and remote (Google Drive) data sources.
  - Synchronization of unit debt information for real-time AI context.
- **Tenant-Scoped Access:** 
  - Strict isolation of data between different organizations and buildings.
  - Residents can only access information related to their own unit or building-wide announcements.

## Non-Functional Requirements (NFR)

- **Security:**
  - **SQL Injection Prevention:** Use of parameterized queries and a dedicated SQL validation layer.
  - **Data Isolation:** Enforced tenant scope filters for all database operations.
  - **RBAC:** Role-based access control to restrict sensitive data access (e.g., separating Resident and Board member permissions).
- **Performance & Scalability:**
  - **Asynchronous Processing:** Built on FastAPI and SQLAlchemy (Async) to handle concurrent user requests efficiently.
  - **Containerization:** Support for Docker/Podman for consistent deployment and scaling.
  - **Caching (Planned):** Redis integration for session management and frequently accessed data.
- **Reliability:**
  - **Error Resilience:** Graceful handling of LLM failures or database timeouts with human-friendly explanations.
  - **Logging:** Comprehensive logging of chat history and AI planning decisions (MongoDB) for auditing and troubleshooting.
- **Privacy:**
  - Minimal personal data collection (primarily phone numbers for linking).
  - Secure storage of chat history and identity mappings.

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

# 🤖 AI Logic (Planning, SQL & Vector Search)

The Copilot uses a hybrid approach for handling user queries, combining structured SQL execution with semantic vector search:

### 1. **Planner (Intent Recognition)**
The LLM receives the user's message, conversation history, and the database schema. It decides if the request needs data from the database (SQL) or if it's a general question that requires searching the building's knowledge base (Vector Search).

### 2. **SQL Execution**
If the planner generates a SQL query:
- **Validation:** The query is checked against a whitelist of tables and security policies.
- **Execution:** Validated queries are executed with automatic **Tenant Isolation** and **RBAC** filters.

### 3. **Vector Search & Embeddings (RAG)**
For questions about house rules, announcements, or general instructions (unstructured data), the system uses **Retrieval-Augmented Generation (RAG)**:

- **Why it's needed:** SQL is great for structured data (debts, residents), but poor for semantic questions like "Can I keep a dog?" or "How to report a leak?". Vector search allows the AI to find relevant text based on *meaning* rather than exact keywords.
- **Data Source:** Knowledge data is imported from external sources (e.g., `knowledge_base.json` from Google Drive) into a **MongoDB `knowledge` collection**.
- **Embedding Process:** During import, the `vectorize_knowledge` service converts text into high-dimensional vectors (embeddings) using **OpenAI (`text-embedding-3-small`)** or **Gemini**.
- **Search:** When a user asks a question, the query is embedded, and a **MongoDB Atlas Vector Search** is performed to find the top 5 most relevant snippets. These snippets are then provided to the LLM (Responder) as context.

### 4. **Responder**
The final answer is crafted by the LLM, combining results from SQL, Vector Search, and the user's personal context. If a query was blocked by security policies, the Responder explains why.

### 🛡️ Security & Privacy Decisions
- **Tenant Isolation:** A `TenantScope` filter is automatically applied to all generated SQL queries, ensuring users can only see data from their own organization.
- **Role-Based Access (RBAC):** The `SQLValidator` uses the user's role (Resident or Board) to enforce access limits. For example, Residents are blocked from bulk neighbor lookups, while Board members have broader selection permissions.
- **Parameterized Queries:** All queries use parameters to prevent SQL injection.
- **Human-Friendly Errors:** Instead of generic "Access Denied" messages, the Responder explains *why* a query was blocked based on policy.

---

# 🔗 Integrations & Data Imports

The system supports automated data imports from external providers (e.g., DAH).

### 📂 Google Drive Integration
The system includes a dedicated `GoogleDriveClient` that can:
- List files in specific Drive folders.
- Automatically find and download the latest data archives (ZIP/Excel).
- Support for Google Service Accounts for secure, non-interactive access.

### 💰 Debt Tracking
Unit debt information is imported and integrated into the AI pipeline:
- **Accurate Terminology:** Replaced "accruals" with "debts" throughout the system to better reflect data meaning.
- **Contextual Awareness:** The user's current balance is included in the LLM prompt context for immediate answers.
- **Queryable Data:** Debt fields are available in the SQL schema for complex queries (e.g., "List apartments with debt > 500").

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
* ✅ Unit Debt import and AI integration
* ✅ Google Drive Client for automated imports
* 🚧 Resident Copilot MVP (in progress)
* 🚧 Context personalization (improving)
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

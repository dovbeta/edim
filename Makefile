# =========================================================
# E-Dim Makefile
# Podman Compose helpers
# =========================================================

COMPOSE=podman compose
API=api
BOT=bot
DB=db

# =========================================================
# CONTAINERS
# =========================================================

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) down
	$(COMPOSE) up -d

build:
	$(COMPOSE) build

rebuild:
	$(COMPOSE) down
	$(COMPOSE) build --no-cache
	$(COMPOSE) up -d

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f

logs-api:
	$(COMPOSE) logs -f $(API)

logs-bot:
	$(COMPOSE) logs -f $(BOT)

# =========================================================
# SHELL
# =========================================================

sh-api:
	$(COMPOSE) exec $(API) bash

sh-bot:
	$(COMPOSE) exec $(BOT) bash

sh-db:
	$(COMPOSE) exec $(DB) bash

# =========================================================
# DATABASE
# =========================================================

db-reset:
	$(COMPOSE) down -v
	$(COMPOSE) up -d

db-shell:
	$(COMPOSE) exec $(DB) psql -U postgres -d app

# =========================================================
# ALEMBIC MIGRATIONS
# =========================================================

db-revision:
	$(COMPOSE) exec $(API) alembic revision --autogenerate -m "$(m)"

db-up:
	$(COMPOSE) exec $(API) alembic upgrade head

db-down:
	$(COMPOSE) exec $(API) alembic downgrade -1

db-current:
	$(COMPOSE) exec $(API) alembic current

db-history:
	$(COMPOSE) exec $(API) alembic history --verbose

# create + apply
db-migrate:
	$(COMPOSE) exec $(API) alembic revision --autogenerate -m "$(m)"
	$(COMPOSE) exec $(API) alembic upgrade head

# apply only
db-apply:
	$(COMPOSE) exec $(API) alembic upgrade head

# =========================================================
# SEED / ADMIN
# =========================================================

seed:
	$(COMPOSE) exec $(API) python -m scripts.seed

create-admin:
	$(COMPOSE) exec $(API) python -m scripts.create_admin

# =========================================================
# DEV HELPERS
# =========================================================

format:
	$(COMPOSE) exec $(API) black .
	$(COMPOSE) exec $(API) isort .

lint:
	$(COMPOSE) exec $(API) ruff check .

# =========================================================
# INFO
# =========================================================

help:
	@echo ""
	@echo "E-Dim Makefile commands:"
	@echo ""
	@echo "  make up            - start containers"
	@echo "  make down          - stop containers"
	@echo "  make rebuild       - rebuild containers"
	@echo ""
	@echo "  make logs          - all logs"
	@echo "  make logs-api      - API logs"
	@echo "  make logs-bot      - Bot logs"
	@echo ""
	@echo "  make sh-api        - shell API container"
	@echo "  make sh-db         - shell DB container"
	@echo ""
	@echo "  make db-migrate m=\"msg\"   - create+apply migration"
	@echo "  make db-revision m=\"msg\"  - create migration"
	@echo "  make db-apply             - apply migrations"
	@echo "  make db-down              - downgrade 1"
	@echo ""
	@echo "  make db-reset      - reset database"
	@echo "  make seed          - seed data"
	@echo ""
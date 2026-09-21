# InVision U: dev commands. Run `make help` for the list.
#
# Everything runs through the project's virtualenv (.venv), so there is no need
# to activate it first. Works from Git Bash, PowerShell and Linux/macOS.

ifeq ($(OS),Windows_NT)
    PY := .venv\Scripts\python.exe
    SYSTEM_PY := python
else
    PY := .venv/bin/python
    SYSTEM_PY := python3
endif

BACKEND_PORT  ?= 8000
FRONTEND_PORT ?= 3000

.DEFAULT_GOAL := help
.PHONY: help venv install install-backend install-frontend env db-init db-reset \
        backend frontend dev test lint build

help:
	@echo "Setup:"
	@echo "  make install        venv + backend/dev deps + frontend deps + backend/.env"
	@echo "  make db-init        migrate SQLite schema and load seed data"
	@echo "  make db-reset       delete the local SQLite file and init again"
	@echo "Run:"
	@echo "  make dev            backend and frontend together (Ctrl+C stops both)"
	@echo "  make backend        FastAPI on http://localhost:$(BACKEND_PORT)"
	@echo "  make frontend       Next.js on http://localhost:$(FRONTEND_PORT)"
	@echo "Checks:"
	@echo "  make test           pytest"
	@echo "  make lint           eslint on the frontend"
	@echo "  make build          production build of the frontend"

# ── Setup ────────────────────────────────────────────────────────────

venv:
	$(SYSTEM_PY) -c "import os, subprocess, sys; os.path.isdir('.venv') or subprocess.check_call([sys.executable, '-m', 'venv', '.venv'])"

install: venv install-backend install-frontend env

install-backend: venv
	$(PY) -m pip install -r backend/requirements.txt -r requirements-dev.txt

install-frontend:
	npm --prefix frontend install

# Copies the template only if backend/.env does not exist yet; never overwrites your key.
env:
	$(SYSTEM_PY) -c "import os, shutil; os.path.exists('backend/.env') or shutil.copy('backend/.env.example', 'backend/.env')"

db-init:
	$(PY) -m backend.db init

db-reset:
	$(PY) -m backend.db reset

# ── Run ──────────────────────────────────────────────────────────────

backend:
	$(PY) -m uvicorn backend.main:app --port $(BACKEND_PORT) --reload

frontend:
	npm --prefix frontend run dev -- --port $(FRONTEND_PORT)

dev:
	$(MAKE) -j2 backend frontend

# ── Checks ───────────────────────────────────────────────────────────

test:
	$(PY) -m pytest -q

lint:
	npm --prefix frontend run lint

build:
	npm --prefix frontend run build

# Backend image. Build context is the repo root (docker-compose.yml sets it):
# alembic.ini lives there, and the code uses absolute `backend.*` imports, so
# the package must sit at /app/backend with /app as the working directory.
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# The decision-memo PDF needs a Unicode TTF for Cyrillic and Kazakh; the slim
# image has none (backend/committee_memo.py looks for DejaVuSans).
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Dependencies first, so a code change does not reinstall them.
COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt

COPY alembic.ini ./
COPY backend ./backend

# SQLite lives on a named volume at /app/var; the directory is created here so
# the volume inherits the non-root owner on first use.
RUN useradd --create-home --uid 10001 app \
    && mkdir -p /app/var \
    && chown -R app:app /app/var
USER app

ENV DATABASE_URL=sqlite:////app/var/invision.db

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"

# `db init` is idempotent (migrate to head, then seed only what is missing), so
# running it on every start is safe and means `docker compose up` is enough.
# One worker only: in-process caches would diverge across workers.
CMD ["sh", "-c", "python -m backend.db init && exec uvicorn backend.main:app --host 0.0.0.0 --port 8000"]

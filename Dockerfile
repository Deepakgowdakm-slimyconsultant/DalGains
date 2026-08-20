# Backend image for Hugging Face Spaces (Docker SDK). See
# scripts/deploy_hf_spaces.md for the full deploy walkthrough.
FROM python:3.11-slim

WORKDIR /app

# System deps for building python packages with native extensions
# (cryptography, pyarrow) -- removed from the final layer via
# --no-install-recommends + apt cache cleanup to keep the image small.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Everything the backend needs to run: src/, alembic config + migrations,
# scripts/, and the checked-in reference data (ingredients, recipes) --
# NOT frontend/, tests/, or per-user runtime data (data/users, data/logs,
# data/dalgains.db), all excluded via .dockerignore.
COPY . .

# HF Spaces' persistent volume for Docker Spaces mounts at /data --
# DATABASE_URL is set to sqlite:////data/dalgains.db in the Space's own
# environment variables (see scripts/deploy_hf_spaces.md step 6), not
# baked into the image, so this directory just needs to exist for the
# default local-dev DATABASE_URL to still work if someone runs this
# image without setting DATABASE_URL at all.
RUN mkdir -p /data

# HF Spaces expects the app to listen on 7860 by default (see this
# README's HF Spaces YAML frontmatter: app_port: 7860).
EXPOSE 7860

# Migrations run once at container start, before uvicorn accepts any
# traffic -- not per-request, and not left as a manual step someone has
# to remember. No --reload (dev-only, would exit repeatedly restarting
# every startup); workers=2 for a small amount of real concurrency on
# HF's free CPU tier without over-committing it.
CMD alembic upgrade head && uvicorn src.api.main:app --host 0.0.0.0 --port 7860 --workers 2

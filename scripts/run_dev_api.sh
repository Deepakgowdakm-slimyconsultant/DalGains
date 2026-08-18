#!/usr/bin/env bash
# Launches the DalGains API locally with auto-reload for development.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f venv/bin/activate ]; then
  source venv/bin/activate
fi

alembic upgrade head
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000

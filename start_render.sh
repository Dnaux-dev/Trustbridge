#!/usr/bin/env bash
# Small launcher for Render that binds to 0.0.0.0 and uses the $PORT env var
set -euo pipefail

# default to 8000 if PORT is not set (useful for local testing)
PORT=${PORT:-8000}

echo "Starting app on 0.0.0.0:${PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --log-level info

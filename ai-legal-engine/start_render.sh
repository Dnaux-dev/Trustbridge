#!/usr/bin/env bash
# Launcher for Render when service root is fastapi/ai-legal-engine
set -euo pipefail

# Default to 8001 for the AI engine if PORT is not set
PORT=${PORT:-8001}

echo "Starting AI-Legal-Engine on 0.0.0.0:${PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --log-level info

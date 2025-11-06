#!/usr/bin/env zsh
set -euo pipefail

# start-dev: start AI engine (background) and main FastAPI app (foreground)
# Usage: ./scripts/start-dev.sh

HERE="$(cd "$(dirname "$0")/.." && pwd)"

cd "$HERE/ai-legal-engine"
echo "Starting AI engine (ai-legal-engine) on http://127.0.0.1:8001"
# export AI_ENGINE_URL if not set so main app can discover it
export AI_ENGINE_URL=${AI_ENGINE_URL:-http://127.0.0.1:8001}

# Start AI engine in background
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload &
AI_PID=$!

# ensure AI engine is terminated when this script exits
trap 'echo "Stopping AI engine..."; kill $AI_PID 2>/dev/null || true' EXIT

cd "$HERE"
echo "Starting main backend (app.main) on http://127.0.0.1:8000"
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

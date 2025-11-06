Render deployment guide — two-service setup (recommended)
=====================================================

Goal: run the main backend and the AI-Legal Engine as two separate Render services. This provides isolation, easier scaling, and fewer dependency conflicts.

Summary (what you'll create on Render)
- Service A: trustbridge-backend (root: `fastapi`) — main API
- Service B: trustbridge-ai-engine (root: `fastapi/ai-legal-engine`) — AI legal engine

Start commands
- Service A (main backend):
  uvicorn app.main:app --host 0.0.0.0 --port 8000
- Service B (AI engine):
  uvicorn app.main:app --host 0.0.0.0 --port 8001

Health checks
- AI engine: use `/api/v1/health` (returns JSON status)
- Main backend: `GET /` returns basic info; you can also use `/users/me` or your auth health check after creating a test user

Environment variables (exact lists)

Service A — trustbridge-backend (fastapi)
- MONGO_URI = mongodb+srv://<user>:<pass>@cluster0.../trustbridge
- JWT_SECRET = <secure random secret> (string, 32+ chars)
- INTERNAL_TOKEN = <shared internal secret> (same value used by Service B for internal calls)
- AI_ENGINE_URL = https://<your-ai-service>.onrender.com  # set to Service B's public URL (or internal hostname if using private networking)
- ACCESS_TOKEN_EXPIRE_MINUTES (optional)

Service B — trustbridge-ai-engine (fastapi/ai-legal-engine)
- GEMINI_API_KEY = <your-google-gemini-api-key>
- GEMINI_MODEL = gemini-2.0-flash (or your preferred model)
- GEMINI_TEMPERATURE = 0.3
- API_SECRET_KEY = <secure random secret, 32+ chars>  # used by ai-engine for its internal security; we recommend matching this to `INTERNAL_TOKEN` used by Service A
- ALLOWED_ORIGINS = https://your-frontend.example.com,http://localhost:3000
- LOG_LEVEL = INFO
- ENVIRONMENT = production

Security note: pick a single long random secret and set both `INTERNAL_TOKEN` (Service A) and `API_SECRET_KEY` (Service B) to that same value — then instruct Service B to validate incoming `X-Internal-Token` headers against `API_SECRET_KEY` (see optional code snippet below). This secures the inter-service calls.

Render-specific steps (UI)
1. Create a new service: trustbridge-ai-engine
   - Repo: your GitHub repo
   - Root directory: fastapi/ai-legal-engine
   - Build & Start: Use Python runtime (Render detects `requirements.txt`).
   - Start command: uvicorn app.main:app --host 0.0.0.0 --port 8001
   - Set environment variables in Render's dashboard (GEMINI_API_KEY, API_SECRET_KEY, ALLOWED_ORIGINS, LOG_LEVEL, ENVIRONMENT). Add any required secrets.
   - Set a health check to `/api/v1/health` (HTTP 200 expected).

2. Create a second service: trustbridge-backend
   - Repo: same repo
   - Root directory: fastapi
   - Start command: uvicorn app.main:app --host 0.0.0.0 --port 8000
   - Set environment variables: MONGO_URI, JWT_SECRET, INTERNAL_TOKEN, AI_ENGINE_URL (point this to the AI engine's public URL provided by Render, e.g. `https://trustbridge-ai-engine.onrender.com`).
   - (Optional) Configure a health check to `/` or an authenticated health endpoint.

3. Ensure `AI_ENGINE_URL` in Service A is the full URL of Service B (include protocol).

Testing and smoke checks
- After both services are live, do these checks:
  - GET https://<ai-service>/api/v1/health → should respond `healthy` or `degraded` JSON
  - GET https://<backend-service>/ → should be reachable
  - Register + login via Service A, call `/recordAction` and verify `ai` field in response (if AI engine returned a result). If `ai` is empty or null, main backend used its local fallback.

Securing inter-service calls (optional code)
If you want Service B to require the internal token for specific endpoints, add a small dependency in `fastapi/ai-legal-engine/app/core/security.py` or similar and use it on the routes that should be internal.

Example (fastapi/ai-legal-engine/app/core/security.py):
```python
from fastapi import Header, HTTPException, status
import os

API_SECRET_KEY = os.getenv('API_SECRET_KEY')

async def internal_only(x_internal_token: str = Header(None)):
    if x_internal_token != API_SECRET_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid internal token')
```

Then import and use as a dependency on private routes in `app/api/routes.py`:
```python
from app.core.security import internal_only

@router.post('/some/internal', dependencies=[Depends(internal_only)])
async def private_endpoint(...):
    ...
```

Why this approach is recommended
- Clear separation of concerns: AI engine can scale independently (CPU/GPU or quota costs) while the main backend stays lightweight.
- Easier debugging and monitoring: logs and metrics per service.
- Fewer dependency/version conflicts (Gemini/LLM libs may need different versions than main app libs).

Alternative: single-container approach
- If you must deploy a single Render service, create a `Dockerfile` and a process manager (supervisord) to run both uvicorn instances in one container. This requires additional configuration and is less flexible. If you need this, tell me and I'll provide a tested Dockerfile.

Local dev tip
- Use the provided `./scripts/start-dev.sh` script to start both services locally (AI on 8001, main backend on 8000). The script also exports `AI_ENGINE_URL` for the main app.

Troubleshooting
- If Service A fails to call the AI engine:
  - Check `AI_ENGINE_URL` in Service A is set to the public Render URL of Service B.
  - Ensure `API_SECRET_KEY` and `INTERNAL_TOKEN` match (if you enforce token checks).
  - Check Service B logs for validation errors or missing GEMINI_API_KEY.

If you want, I can also:
- Provide a `Dockerfile` and supervisor config to run both services in one container (single-service Render deployment).
- Add the `internal_only` dependency to the ai-engine code for you and wire it to `API_SECRET_KEY`.

---
Change log: created on 2025-11-06 to document two-service Render deployment and security recommendations.

# TrustBridge FastAPI Backend

This is an async FastAPI backend using Motor (async MongoDB) implementing core TrustBridge functionality:

- JWT-based authentication (citizen, business, admin)
- User registration and token issuance
- Append-only ledger for actions with AI analysis
- Mock AI analyzer (replaceable with an LLM or rules engine)
- Endpoints matching the requested spec

Quick start

1. Create and activate a Python venv.

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
uvicorn app.main:app --reload --port 8000
```

Environment variables (optional):
- MONGO_URI
- JWT_SECRET
- INTERNAL_TOKEN

Endpoints implemented (high level):
- POST /registerUser
- POST /login
- GET /users/me
- GET /users/{user_id}/ledger
- GET /companies
- GET /companies/{id}
- POST /companies/{id}/consent
- POST /company/audit
- POST /recordAction
- POST /ai/analyzeAction (internal, needs header X-Internal-Token)
- GET /getLedger (admin)
- GET /actions (admin)
- POST /ledger/append (admin/internal)

# 🏛️ TrustBridge AI-Legal Engine

AI-powered NDPR/NDPA compliance analysis for Nigerian businesses using Google Gemini.

## ✨ Features

- 📋 **Privacy Policy Analysis** - Comprehensive NDPA 2023 compliance checking
- ⚖️ **Citizen Action Validation** - Validate data subject rights requests
- 🔍 **Quick Compliance Checks** - Rapid risk assessment for business practices
- 🤖 **AI-Generated Fixes** - Actionable remediation steps with legal references

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Google Gemini API key (free at https://makersuite.google.com)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo>
cd trustbridge-legal-engine
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

5. **Run the server**
```bash
python -m app.main
# Or: uvicorn app.main:app --reload
```

6. **Access the API**
- Swagger Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

## 📚 API Endpoints

### Policy Analysis
```bash
POST /api/v1/analyze/policy
```

### Citizen Action Validation
```bash
POST /api/v1/validate/action
```

### Quick Compliance Check
```bash
POST /api/v1/check/compliance
```

## 🧪 Running Tests
```bash
pytest tests/ -v
```

## 📖 Documentation

Full API documentation available at `/docs` when server is running.

## 🛡️ Security

- Never commit `.env` file
- Change `API_SECRET_KEY` in production
- Use environment-specific configurations
- Enable rate limiting for production

## 📄 License

[Your License Here]

## 🧩 Frontend integration (CORS and examples)

If you want to call the AI engine directly from browser-based frontends, you need to ensure CORS is configured correctly on the AI service.

- For development or public demos you can enable wildcard CORS by setting `ALLOW_ALL_ORIGINS=true` in the AI engine environment (see `DEPLOYMENT_RENDER.md`).
- For production, prefer `ALLOWED_ORIGINS=https://your-frontend.example.com` and keep `ALLOW_ALL_ORIGINS=false`.

Below are copy-pasteable examples for the frontend team.

1) Simple curl (server-to-server)

```bash
curl -i -X POST https://<ai-engine-host>/api/v1/validate/action \
	-H "Content-Type: application/json" \
	-d '{"action_type":"REVOKE_CONSENT","citizen_id":"citizen-123","company_id":"company-1","company_name":"Acme Ltd","data_types":["email"],"reason":"I withdraw consent"}'
```

2) Browser fetch (no internal token, CORS enabled)

```javascript
// Example using fetch from a browser frontend (works when CORS allows your origin)
const payload = {
	action_type: 'REVOKE_CONSENT',
	citizen_id: 'citizen-123',
	company_id: 'company-1',
	company_name: 'Acme Ltd',
	data_types: ['email'],
	reason: 'I withdraw consent'
};

const res = await fetch('https://<ai-engine-host>/api/v1/validate/action', {
	method: 'POST',
	mode: 'cors',
	headers: {
		'Content-Type': 'application/json'
	},
	body: JSON.stringify(payload)
});

if (!res.ok) {
	const text = await res.text();
	throw new Error(`AI engine error: ${res.status} ${text}`);
}

const data = await res.json();
console.log('AI validation result', data);
```

3) Browser fetch with internal token (if AI engine enforces an internal header)

If your deployment enforces an internal token (recommended for private endpoints), include the `X-Internal-Token` header. Make sure you **do not** expose long-lived secrets in public browser code. Use this only from trusted server-side code or short-lived tokens issued by your backend.

```javascript
const internalToken = '<INTERNAL_TOKEN_FROM_BACKEND>'; // do NOT embed this in public JS

const res = await fetch('https://<ai-engine-host>/api/v1/validate/action', {
	method: 'POST',
	mode: 'cors',
	headers: {
		'Content-Type': 'application/json',
		'X-Internal-Token': internalToken
	},
	body: JSON.stringify(payload)
});

// handle response as above
```

4) Troubleshooting CORS problems

- If the browser console shows CORS errors, confirm that the AI service's `ALLOW_ALL_ORIGINS` or `ALLOWED_ORIGINS` includes your frontend origin.
- Make sure the frontend request includes only allowed headers; custom headers (like `X-Internal-Token`) trigger a preflight OPTIONS request that the server must accept. Our FastAPI CORS middleware allows `*` headers when configured.
- For local testing, you can temporarily enable `ALLOW_ALL_ORIGINS=true` on Render. Remember to turn it off for production and instead list allowed origins explicitly.

If you want, I can add a tiny example frontend `example_frontend.html` in the repo that demonstrates these calls.
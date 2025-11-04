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
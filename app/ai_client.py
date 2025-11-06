import os
import asyncio
from typing import Optional, Dict, Any
import httpx

AI_ENGINE_URL = os.getenv('AI_ENGINE_URL', '').rstrip('/') or None
INTERNAL_TOKEN = os.getenv('INTERNAL_TOKEN', 'internal-secret-token')


async def _post(path: str, payload: dict, timeout: int = 15) -> Optional[Dict[str, Any]]:
    """Internal helper to POST to the AI engine and return JSON or None on failure."""
    if not AI_ENGINE_URL:
        return None
    url = f"{AI_ENGINE_URL}{path}"
    headers = {'Content-Type': 'application/json', 'X-Internal-Token': INTERNAL_TOKEN}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            # non-200 -> treat as no-AI available
            return None
    except (httpx.RequestError, httpx.HTTPStatusError):
        return None


def _map_action_type(action_type: str) -> str:
    """Map project action types to the AI engine's ActionType where possible.
    This is a best-effort mapping; the AI engine accepts a limited enum set.
    """
    if not action_type:
        return 'consent_revoked'
    a = action_type.lower()
    if 'revoke' in a or 'withdraw' in a:
        return 'consent_revoked'
    if 'grant' in a:
        return 'consent_granted'
    if 'access' in a or 'request_access' in a:
        return 'data_access'
    if 'delete' in a or 'deletion' in a or 'erasure' in a:
        return 'data_deletion'
    return 'consent_revoked'


async def validate_citizen_action(action_type: str, company_id: str, details: dict = None, citizen_id: str = 'unknown') -> Optional[dict]:
    """Call the AI engine to validate a citizen action.

    Returns the parsed JSON response from the AI engine or None if the engine
    is not configured or the call failed.
    """
    if not AI_ENGINE_URL:
        return None
    payload = {
        'action_type': _map_action_type(action_type),
        'citizen_id': citizen_id or 'unknown',
        'company_id': company_id or 'unknown',
        'company_name': str(company_id or 'unknown'),
        'data_types': details.get('data_types') if details and isinstance(details.get('data_types'), list) and details.get('data_types') else ['personal_data'],
        'reason': details.get('reason') if details else None
    }
    return await _post('/api/v1/validate/action', payload)


async def analyze_policy(company_name: str, document_text: str, industry: Optional[str] = None) -> Optional[dict]:
    """Call the AI engine's policy analysis endpoint.

    Returns parsed JSON response or None on failure.
    """
    if not AI_ENGINE_URL:
        return None
    payload = {
        'document_text': document_text,
        'company_name': company_name or 'unknown',
        'industry': industry or ''
    }
    return await _post('/api/v1/analyze/policy', payload, timeout=60)

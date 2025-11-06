from datetime import datetime
import os
from typing import Optional

# try to use the external AI engine via HTTP when configured; otherwise fall back
from . import ai_client


async def analyze_action(user_action: str, company_id: str = None, details: dict = None, actor_id: str = None) -> dict:
    """Analyze an action using the ai-legal-engine when available, with
    a deterministic local fallback otherwise.

    Returns a dict with keys: advice, risk, suggestions, timestamp, raw
    """
    # If an external AI engine is configured, try it first
    try:
        ai_result = await ai_client.validate_citizen_action(user_action, company_id, details or {}, citizen_id=(actor_id or 'unknown'))
        if ai_result:
            # ai_engine returns a structured response for action validation; normalize
            return {
                'advice': ai_result.get('plain_explanation') or ai_result.get('legal_explanation') or 'See AI response',
                'risk': 'medium' if ai_result.get('is_legal') is False else 'low',
                'suggestions': ai_result.get('next_steps') or [],
                'timestamp': datetime.utcnow().isoformat(),
                'raw': {'ai_response': ai_result}
            }
    except Exception:
        # swallow and fall through to local analyzer
        pass

    # Local deterministic fallback
    text = (user_action or '') + ' ' + (details.get('text') if details else '')
    text = text.lower()
    risk = 'low'
    advice = 'No issues detected.'
    suggestions = []

    if any(k in text for k in ['revoke', 'withdraw']):
        advice = 'Revocation noted; ensure controller stops processing.'
        risk = 'low'
        suggestions = ['Confirm deletion schedule', 'Notify processors']
    if 'policy' in text and ('missing' in text or 'lack' in text or 'not' in text):
        advice = 'Policy may lack explicit consent language.'
        risk = 'medium'
        suggestions = ['Add explicit consent clause', 'Provide opt-out']
    if any(k in text for k in ['transfer', 'third-party', 'cross-border']):
        advice = 'Cross-border transfer detected; check safeguards.'
        risk = 'high'
        suggestions = ['SCCs or equivalent', 'Document legal basis']

    return {
        'advice': advice,
        'risk': risk,
        'suggestions': suggestions,
        'timestamp': datetime.utcnow().isoformat(),
        'raw': {'user_action': user_action, 'company_id': company_id, 'details': details}
    }

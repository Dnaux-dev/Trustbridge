from datetime import datetime

async def analyze_action(user_action: str, company_id: str = None, details: dict = None):
    # Simple deterministic mock — replace with LLM/rules engine
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

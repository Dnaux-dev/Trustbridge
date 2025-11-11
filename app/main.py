from fastapi import FastAPI, Depends, HTTPException, status, Header, Body, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .db import connect, close
from . import db as db_module
from .schemas import UserCreate, Token, UserOut, Company, ActionIn, AIResult, LedgerEntryOut, RecordActionResponse, ActionOut
from .auth import get_password_hash, verify_password, create_access_token, get_current_user, require_role, internal_only
from .ai import analyze_action
from bson import ObjectId
import datetime

app = FastAPI(title='TrustBridge FastAPI Backend')

# Configure CORS depending on ALLOWED_ORIGINS environment variable.
# If ALLOWED_ORIGINS is set (comma-separated), use that explicit list and enable credentials
# which is required for cookie-based auth. If not set, fall back to wildcard origins and
# disable credentials (browser-compatible but disallows cookies).
from .config import ALLOWED_ORIGINS as _ALLOWED_ORIGINS
if _ALLOWED_ORIGINS and _ALLOWED_ORIGINS.strip():
    _origins = [o.strip() for o in _ALLOWED_ORIGINS.split(',') if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*']
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=False,
        allow_methods=['*'],
        allow_headers=['*']
    )


@app.on_event('startup')
async def startup_db():
    try:
        # connect() is async and will ping the server; fail-fast if Mongo is unreachable
        await connect()
        print('Connected to MongoDB')
    except Exception as e:
        # Provide a clear startup error rather than a deep traceback later
        import traceback, sys
        traceback.print_exc()
        print('Failed to connect to MongoDB. Please check MONGO_URI and ensure MongoDB is running.', file=sys.stderr)
        # Re-raise to stop the application startup
        raise


@app.on_event('shutdown')
async def shutdown_db():
    close()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler that ensures responses include CORS headers.

    This helps the browser show the underlying error instead of a silent CORS block
    when an internal server error occurs (for example, DB connection failures).
    """
    import traceback, sys
    traceback.print_exc()
    # Use wildcard origin so responses are accepted from any frontend origin.
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'false',
        'Access-Control-Allow-Methods': '*',
        'Access-Control-Allow-Headers': '*'
    }
    # In DEBUG mode, include the exception message to help debugging (development only).
    from .config import DEBUG as _DEBUG
    detail = 'Internal Server Error'
    if _DEBUG:
        try:
            detail = f"{exc.__class__.__name__}: {str(exc)}"
        except Exception:
            detail = 'Internal Server Error'
    # Return a JSON 500 with the CORS headers set so the browser receives it
    return JSONResponse(status_code=500, content={'detail': detail}, headers=headers)


def oid(id_str):
    try:
        return ObjectId(id_str)
    except Exception:
        return None


@app.post('/registerUser', response_model=UserOut, summary="Register a new user")
async def register_user(payload: UserCreate):
    # Ensure DB is connected
    if getattr(db_module, 'db', None) is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='Database not available')
    try:
        # check existing
        existing = await db_module.db['users'].find_one({'email': payload.email})
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Email already registered')
        pwd = get_password_hash(payload.password)
        user_doc = {
            'name': payload.name,
            'email': payload.email,
            'password': pwd,
            'role': payload.role,
            'company': payload.company
        }
        result = await db_module.db['users'].insert_one(user_doc)
        user_doc['id'] = str(result.inserted_id)
        return UserOut(id=user_doc['id'], name=user_doc['name'], email=user_doc['email'], role=user_doc['role'], company=user_doc.get('company'))
    except HTTPException:
        # Re-raise expected HTTPExceptions
        raise
    except Exception as e:
        # Log and return a clear server error (include error text for debugging)
        import traceback
        traceback.print_exc()
        # Include the exception message in the HTTP response detail to aid debugging.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Failed to create user: {str(e)}')


@app.post('/login', response_model=Token, summary="Login and receive a JWT token")
async def login(form: dict = Body(..., example={"email":"alice@example.com","password":"sup3rsecret"})):
    # accept JSON {"email":"..","password":".."}
    email = form.get('email')
    password = form.get('password')
    if not email or not password:
        raise HTTPException(status_code=400, detail='email and password required')
    user = await db_module.db['users'].find_one({'email': email})
    if not user:
        raise HTTPException(status_code=401, detail='Invalid credentials')
    if not verify_password(password, user['password']):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    token = create_access_token({'sub': str(user['_id']), 'role': user.get('role')})
    return {'access_token': token, 'token_type': 'bearer'}


@app.get('/users/me', response_model=UserOut, summary="Get current authenticated user")
async def users_me(user: dict = Depends(get_current_user)):
    return UserOut(id=str(user['_id']), name=user['name'], email=user['email'], role=user['role'], company=user.get('company'))


@app.get('/users/{user_id}/ledger', response_model=list[LedgerEntryOut], summary="Get ledger entries for a user")
async def user_ledger(user_id: str, current: dict = Depends(get_current_user)):
    # allow self, admin, or business
    if current.get('role') != 'admin' and str(current.get('_id')) != user_id and current.get('role') != 'business':
        # business may be allowed only for their users — kept permissive per spec but can lock down
        if current.get('role') != 'business':
            raise HTTPException(status_code=403, detail='Forbidden')
    entries = []
    cursor = db_module.db['ledger'].find({'actor': ObjectId(user_id)}).sort('timestamp', -1)
    async for doc in cursor:
        doc['id'] = str(doc['_id'])
        doc['actor'] = str(doc['actor']) if doc.get('actor') else None
        doc['company'] = str(doc['company']) if doc.get('company') else None
        entries.append(doc)
    return entries


@app.get('/companies', response_model=list[Company], summary="List companies")
async def list_companies(user: dict = Depends(get_current_user)):
    out = []
    async for c in db_module.db['companies'].find():
        out.append(Company(id=str(c['_id']), name=c.get('name'), description=c.get('description'), contactEmail=c.get('contactEmail'), policies=c.get('policies')))
    return out


@app.get('/companies/{company_id}', response_model=Company, summary="Get a single company")
async def get_company(company_id: str, user: dict = Depends(get_current_user)):
    c = await db_module.db['companies'].find_one({'_id': oid(company_id)})
    if not c:
        raise HTTPException(status_code=404, detail='Company not found')
    return Company(id=str(c['_id']), name=c.get('name'), description=c.get('description'), contactEmail=c.get('contactEmail'), policies=c.get('policies'))


@app.post('/companies/{company_id}/consent', response_model=RecordActionResponse, summary="Grant or revoke consent for a company (citizen only)")
async def company_consent(company_id: str, payload: dict = Body(..., example={"action":"revoke","details":{"reason":"no longer using service"}}), user: dict = Depends(require_role('citizen'))):
    # expect { action: 'grant' | 'revoke', details: {} }
    action = payload.get('action')
    if action not in ('grant', 'revoke'):
        raise HTTPException(status_code=400, detail='Invalid action')
    # record action via recordAction flow
    ai = await analyze_action(f'{action}_consent', company_id, payload.get('details'))
    action_doc = {
        'actor': ObjectId(str(user['_id'])),
        'actorRole': user.get('role'),
        'type': f'{action}_consent',
        'details': payload.get('details'),
        'company': oid(company_id),
        'createdAt': datetime.datetime.utcnow()
    }
    res = await db_module.db['actions'].insert_one(action_doc)
    ledger_doc = {
        'actionRef': res.inserted_id,
        'actor': action_doc['actor'],
        'actorRole': action_doc['actorRole'],
        'actionType': action_doc['type'],
        'company': action_doc['company'],
        'timestamp': datetime.datetime.utcnow(),
        'aiReport': ai,
        'raw': {'source': 'consent_endpoint', 'payload': payload}
    }
    await db_module.db['ledger'].insert_one(ledger_doc)
    return RecordActionResponse(actionId=str(res.inserted_id), ai=ai)


@app.post('/company/audit', response_model=AIResult, summary="Run a company policy audit (business only)")
async def company_audit(payload: dict = Body(..., example={"policyText":"Our privacy policy says..."}), user: dict = Depends(require_role('business'))):
    # business user must have company
    company_id = user.get('company')
    if not company_id:
        raise HTTPException(status_code=400, detail='User not associated with a company')
    policy = payload.get('policyText') or payload.get('policy')
    ai = await analyze_action('company_audit', company_id, {'policyText': policy})
    # Append to ledger
    audit_doc = {
        'actor': ObjectId(str(user['_id'])),
        'actorRole': user.get('role'),
        'type': 'company_audit',
        'details': {'policy': policy},
        'company': oid(company_id),
        'createdAt': datetime.datetime.utcnow()
    }
    res = await db_module.db['actions'].insert_one(audit_doc)
    ledger_doc = {
        'actionRef': res.inserted_id,
        'actor': audit_doc['actor'],
        'actorRole': audit_doc['actorRole'],
        'actionType': audit_doc['type'],
        'company': audit_doc['company'],
        'timestamp': datetime.datetime.utcnow(),
        'aiReport': ai,
        'raw': {'source': 'company_audit', 'payload': payload}
    }
    await db_module.db['ledger'].insert_one(ledger_doc)
    return ai


@app.post('/recordAction', response_model=RecordActionResponse, summary="Record a user action (citizen or business)")
async def record_action(payload: ActionIn, user: dict = Depends(require_role('citizen', 'business'))):
    # call AI analyzer
    ai = await analyze_action(payload.type, payload.companyId, payload.details)
    action_doc = {
        'actor': ObjectId(str(user['_id'])),
        'actorRole': user.get('role'),
        'type': payload.type,
        'details': payload.details,
        'company': oid(payload.companyId) if payload.companyId else None,
        'createdAt': datetime.datetime.utcnow()
    }
    res = await db_module.db['actions'].insert_one(action_doc)
    ledger_doc = {
        'actionRef': res.inserted_id,
        'actor': action_doc['actor'],
        'actorRole': action_doc['actorRole'],
        'actionType': action_doc['type'],
        'company': action_doc['company'],
        'timestamp': datetime.datetime.utcnow(),
        'aiReport': ai,
        'raw': {'request': payload.dict()}
    }
    await db_module.db['ledger'].insert_one(ledger_doc)
    return RecordActionResponse(actionId=str(res.inserted_id), ai=ai)


@app.post('/ai/analyzeAction', response_model=AIResult, summary="Internal AI analysis endpoint (internal token required)")
async def ai_analyze(payload: dict = Body(..., example={"user_action":"revoke_consent","company_id":"5f8d0d55","details":{"text":"Please delete my data"}}), _=Depends(internal_only)):
    # internal endpoint protected by header X-Internal-Token
    user_action = payload.get('user_action')
    company_id = payload.get('company_id')
    details = payload.get('details')
    ai = await analyze_action(user_action, company_id, details)
    return ai


@app.get('/getLedger', response_model=list[LedgerEntryOut], summary="Get the full ledger (admin only)")
async def get_ledger(current: dict = Depends(get_current_user)):
    # admin only
    if current.get('role') != 'admin':
        raise HTTPException(status_code=403, detail='Admin only')
    out = []
    cursor = db_module.db['ledger'].find().sort('timestamp', -1)
    async for doc in cursor:
        doc['id'] = str(doc['_id'])
        doc['actor'] = str(doc['actor']) if doc.get('actor') else None
        doc['company'] = str(doc['company']) if doc.get('company') else None
        out.append(doc)
    return out


@app.get('/actions', response_model=list[ActionOut], summary="List actions (admin only)")
async def get_actions(current: dict = Depends(get_current_user)):
    if current.get('role') != 'admin':
        raise HTTPException(status_code=403, detail='Admin only')
    out: list[ActionOut] = []
    cursor = db_module.db['actions'].find().sort('createdAt', -1)
    async for doc in cursor:
        out.append(ActionOut(id=str(doc.get('_id')), actor=str(doc.get('actor')) if doc.get('actor') else None, actorRole=doc.get('actorRole'), type=doc.get('type'), details=doc.get('details'), company=str(doc.get('company')) if doc.get('company') else None, createdAt=doc.get('createdAt')))
    return out


@app.post('/ledger/append', response_model=dict, summary="Append a raw document to the ledger (admin or internal token)")
async def ledger_append(payload: dict = Body(...), current: dict = Depends(get_current_user), x_internal_token: str = Header(None)):
    # allow admin or internal token
    if current.get('role') != 'admin' and x_internal_token != None:
        # if no admin, require internal token
        raise HTTPException(status_code=403, detail='Admin or internal token required')
    doc = payload.copy()
    doc['timestamp'] = datetime.datetime.utcnow()
    res = await db_module.db['ledger'].insert_one(doc)
    return {'id': str(res.inserted_id)}

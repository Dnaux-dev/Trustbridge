from motor.motor_asyncio import AsyncIOMotorClient
from .config import MONGO_URI

client = None
db = None

async def connect():
    """Create Motor client, set module-level db and verify server with ping.

    Raises on failure so the application can fail-fast during startup.
    """
    global client, db
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.get_default_database()
    # verify connection with a ping — will raise if server unreachable
    try:
        await client.admin.command('ping')
    except Exception:
        # cleanup on failure
        try:
            client.close()
        except Exception:
            pass
        client = None
        db = None
        raise
    return db

def close():
    global client
    if client:
        client.close()

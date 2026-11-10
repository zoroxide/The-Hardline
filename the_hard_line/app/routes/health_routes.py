from fastapi import APIRouter
from app.database import get_db_pool

router = APIRouter(tags=["Health"])

@router.get("/healthz")
async def health_check():
    db_connected = False
    try:
        pool = get_db_pool()
        async with pool.acquire() as conn:
            val = await conn.fetchval("SELECT 1;")
            db_connected = (val == 1)
    except Exception:
        db_connected = False

    return {
        "status": "healthy" if db_connected else "degraded",
        "app": "The Hardline",
        "database": "connected" if db_connected else "disconnected"
    }

import asyncpg
from typing import Optional
from app.config import DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME

_pool: Optional[asyncpg.Pool] = None

async def init_db_pool() -> asyncpg.Pool:
    """Initialize the asynchronous PostgreSQL connection pool."""
    global _pool
    if _pool is None:
        print(f"[Database] Connecting to {DB_HOST}:{DB_PORT}/{DB_NAME}...")
        _pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            min_size=1,
            max_size=4,
            ssl=False,
            command_timeout=15.0
        )
        print("[Database] AsyncPG connection pool initialized successfully.")
    return _pool

async def close_db_pool() -> None:
    """Close the asynchronous PostgreSQL connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        print("[Database] AsyncPG connection pool closed.")

def get_db_pool() -> asyncpg.Pool:
    """Retrieve the active database connection pool."""
    if _pool is None:
        raise RuntimeError("Database connection pool is not initialized.")
    return _pool

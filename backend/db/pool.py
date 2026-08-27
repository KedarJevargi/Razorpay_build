import os
import asyncpg
from typing import Optional

_pool: Optional[asyncpg.Pool] = None

async def init_pool():
    global _pool
    if _pool is None:
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/commerce")
        _pool = await asyncpg.create_pool(db_url)
    return _pool

async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        await init_pool()
    return _pool

async def close_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

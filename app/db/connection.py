import asyncpg
from typing import Optional, Any
from contextlib import asynccontextmanager
from app.config import get_settings
from app.utils.observability import get_logger

settings = get_settings()
logger = get_logger(__name__)


class Database:
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        if self._pool is not None:
            return
        self._pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=settings.db_pool_min_size,
            max_size=settings.db_pool_max_size,
            command_timeout=settings.db_command_timeout_seconds,
        )
        logger.info(
            "database_pool_created",
            min_size=settings.db_pool_min_size,
            max_size=settings.db_pool_max_size,
        )

    async def disconnect(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("database_pool_closed")

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        return self._pool

    @asynccontextmanager
    async def acquire(self):
        async with self.pool.acquire() as connection:
            yield connection

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> Optional[asyncpg.Record]:
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def execute(self, query: str, *args: Any) -> str:
        async with self.acquire() as conn:
            return await conn.execute(query, *args)

    async def health_check(self) -> bool:
        try:
            result = await self.fetchval("SELECT 1")
            return result == 1
        except Exception as e:
            logger.error("database_health_check_failed", error=str(e))
            return False


database = Database()

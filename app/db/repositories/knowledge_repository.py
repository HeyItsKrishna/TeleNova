from typing import List, Optional

from app.db.connection import Database
from app.utils.observability import get_logger

logger = get_logger(__name__)


class KnowledgeRepository:

    def __init__(self, db: Database):
        self._db = db

    async def save_chunk(
        self,
        id: str,
        chunk_text: str,
        source: str,
        filepath: str,
        chunk_index: int,
    ) -> str:
        return await self._db.execute(
            """
            INSERT INTO knowledge_chunks (
                id,
                chunk_text,
                source,
                filepath,
                chunk_index
            )
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id)
            DO UPDATE
            SET
                chunk_text = EXCLUDED.chunk_text,
                source = EXCLUDED.source,
                filepath = EXCLUDED.filepath,
                chunk_index = EXCLUDED.chunk_index
            """,
            id,
            chunk_text,
            source,
            filepath,
            chunk_index,
        )

    async def save_chunks(self, chunks: List[dict]) -> None:
        async with self._db.transaction() as conn:
            for chunk in chunks:
                await conn.execute(
                    """
                    INSERT INTO knowledge_chunks (
                        id,
                        chunk_text,
                        source,
                        filepath,
                        chunk_index
                    )
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (id)
                    DO UPDATE
                    SET
                        chunk_text = EXCLUDED.chunk_text,
                        source = EXCLUDED.source,
                        filepath = EXCLUDED.filepath,
                        chunk_index = EXCLUDED.chunk_index
                    """,
                    chunk["id"],
                    chunk["chunk_text"],
                    chunk["source"],
                    chunk["filepath"],
                    chunk["chunk_index"],
                )

    async def get_chunk_by_id(self, id: str) -> Optional[dict]:
        row = await self._db.fetchrow(
            """
            SELECT
                id,
                chunk_text,
                source,
                filepath,
                chunk_index
            FROM knowledge_chunks
            WHERE id = $1
            """,
            id,
        )

        return dict(row) if row else None

    async def get_chunks_by_ids(self, ids: List[str]) -> List[dict]:
        rows = await self._db.fetch(
            """
            SELECT
                id,
                chunk_text,
                source,
                filepath,
                chunk_index
            FROM knowledge_chunks
            WHERE id = ANY($1)
            """,
            ids,
        )

        return [dict(row) for row in rows]

    async def get_all_chunk_ids(self) -> List[str]:
        rows = await self._db.fetch(
            """
            SELECT id
            FROM knowledge_chunks
            ORDER BY id
            """
        )

        return [row["id"] for row in rows]

    async def delete_all_chunks(self) -> str:
        return await self._db.execute(
            """
            DELETE FROM knowledge_chunks
            """
        )

    async def count_chunks(self) -> int:
        value = await self._db.fetchval(
            """
            SELECT COUNT(*)
            FROM knowledge_chunks
            """
        )

        return value if value is not None else 0
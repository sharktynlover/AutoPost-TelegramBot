from __future__ import annotations

import aiosqlite
from datetime import datetime

from .models import Post


class PostRepository:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def init(self) -> None:
        self._conn = await aiosqlite.connect(self._db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                photo_file_id TEXT,
                run_at TEXT NOT NULL,
                send_to_tg INTEGER NOT NULL,
                send_to_vk INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError('Database is not initialized')
        return self._conn

    async def create_post(
        self,
        text: str,
        photo_file_id: str | None,
        run_at: datetime,
        send_to_tg: bool,
        send_to_vk: bool,
    ) -> int:
        cursor = await self.conn.execute(
            '''
            INSERT INTO posts (text, photo_file_id, run_at, send_to_tg, send_to_vk)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (text, photo_file_id, run_at.isoformat(), int(send_to_tg), int(send_to_vk)),
        )
        await self.conn.commit()
        return int(cursor.lastrowid)

    async def get_post(self, post_id: int) -> Post | None:
        cursor = await self.conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._map_row(row)

    async def list_pending(self) -> list[Post]:
        cursor = await self.conn.execute(
            "SELECT * FROM posts WHERE status = 'pending' ORDER BY run_at ASC"
        )
        rows = await cursor.fetchall()
        return [self._map_row(row) for row in rows]

    async def mark_done(self, post_id: int) -> None:
        await self.conn.execute('UPDATE posts SET status = ? WHERE id = ?', ('done', post_id))
        await self.conn.commit()

    async def mark_failed(self, post_id: int) -> None:
        await self.conn.execute('UPDATE posts SET status = ? WHERE id = ?', ('failed', post_id))
        await self.conn.commit()

    async def mark_cancelled(self, post_id: int) -> None:
        await self.conn.execute('UPDATE posts SET status = ? WHERE id = ?', ('cancelled', post_id))
        await self.conn.commit()

    def _map_row(self, row: aiosqlite.Row) -> Post:
        return Post(
            id=int(row['id']),
            text=str(row['text']),
            photo_file_id=row['photo_file_id'],
            run_at=datetime.fromisoformat(str(row['run_at'])),
            send_to_tg=bool(row['send_to_tg']),
            send_to_vk=bool(row['send_to_vk']),
            status=str(row['status']),
        )

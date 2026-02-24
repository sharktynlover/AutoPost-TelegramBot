from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from aiogram import Bot

from src.db import PostRepository
from src.services.publisher import Publisher

logger = logging.getLogger(__name__)


class PostScheduler:
    def __init__(
        self,
        repo: PostRepository,
        publisher: Publisher,
        bot: Bot,
        timezone: ZoneInfo,
    ) -> None:
        self._repo = repo
        self._publisher = publisher
        self._bot = bot
        self._timezone = timezone
        self._scheduler = AsyncIOScheduler(timezone=timezone)

    async def start_and_restore(self) -> None:
        self._scheduler.start()
        posts = await self._repo.list_pending()
        for post in posts:
            if post.run_at > datetime.now(self._timezone):
                self._schedule(post.id, post.run_at)

    async def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    async def schedule_post(self, post_id: int) -> None:
        post = await self._repo.get_post(post_id)
        if post is None or post.status != 'pending':
            return
        self._schedule(post.id, post.run_at)

    async def run_now(self, post_id: int) -> tuple[bool, str]:
        post = await self._repo.get_post(post_id)
        if post is None:
            return False, 'Пост не найден.'
        if post.status != 'pending':
            return False, f'Пост уже имеет статус: {post.status}.'

        self._remove_job(post_id)
        await self._dispatch(post_id)
        return True, 'Пост отправлен досрочно.'

    async def cancel(self, post_id: int) -> tuple[bool, str]:
        post = await self._repo.get_post(post_id)
        if post is None:
            return False, 'Пост не найден.'
        if post.status != 'pending':
            return False, f'Пост уже имеет статус: {post.status}.'

        self._remove_job(post_id)
        await self._repo.mark_cancelled(post_id)
        return True, 'Пост удален из плана.'

    def _schedule(self, post_id: int, run_at: datetime) -> None:
        self._scheduler.add_job(
            self._dispatch,
            trigger=DateTrigger(run_date=run_at),
            id=f'post-{post_id}',
            args=[post_id],
            replace_existing=True,
            misfire_grace_time=300,
        )

    def _remove_job(self, post_id: int) -> None:
        try:
            self._scheduler.remove_job(f'post-{post_id}')
        except JobLookupError:
            pass

    async def _dispatch(self, post_id: int) -> None:
        post = await self._repo.get_post(post_id)
        if post is None or post.status != 'pending':
            return

        try:
            await self._publisher.publish_post(post=post, bot=self._bot)
            await self._repo.mark_done(post.id)
            logger.info('Post %s sent', post.id)
        except Exception:
            logger.exception('Failed to send post %s', post.id)
            await self._repo.mark_failed(post.id)

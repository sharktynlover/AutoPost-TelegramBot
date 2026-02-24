from __future__ import annotations

from aiogram import Bot

from src.models import Post
from src.services.telegram_publisher import TelegramPublisher
from src.services.vk_publisher import VKPublisher


class Publisher:
    def __init__(self, tg_publisher: TelegramPublisher, vk_publisher: VKPublisher) -> None:
        self._tg = tg_publisher
        self._vk = vk_publisher

    async def publish_post(self, post: Post, bot: Bot) -> None:
        if post.send_to_tg:
            await self._tg.publish(
                bot=bot,
                text=post.text,
                photo_file_id=post.photo_file_id,
            )

        if post.send_to_vk:
            await self._vk.publish(
                bot=bot,
                text=post.text,
                tg_photo_file_id=post.photo_file_id,
            )

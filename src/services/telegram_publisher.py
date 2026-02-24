from __future__ import annotations

from aiogram import Bot


class TelegramPublisher:
    def __init__(self, channels: list[str]) -> None:
        self._channels = [channel.strip() for channel in channels if channel.strip()]
        self._chat_id_cache: dict[str, int | str] = {}

    async def _resolve_chat_id(self, bot: Bot, raw_channel: str) -> int | str:
        cached = self._chat_id_cache.get(raw_channel)
        if cached is not None:
            return cached

        if raw_channel.lstrip('-').isdigit():
            resolved: int | str = int(raw_channel)
        else:
            try:
                chat = await bot.get_chat(raw_channel)
                resolved = int(chat.id)
            except Exception:
                # Fallback for unusual channel identifiers.
                resolved = raw_channel

        self._chat_id_cache[raw_channel] = resolved
        return resolved

    async def publish(self, bot: Bot, text: str, photo_file_id: str | None) -> None:
        seen_chat_ids: set[int | str] = set()
        for raw_channel in self._channels:
            channel = await self._resolve_chat_id(bot, raw_channel)
            if channel in seen_chat_ids:
                continue
            seen_chat_ids.add(channel)

            if photo_file_id:
                await bot.send_photo(
                    chat_id=channel,
                    photo=photo_file_id,
                    caption=text,
                )
            else:
                await bot.send_message(chat_id=channel, text=text)

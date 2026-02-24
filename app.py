import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.bot.handlers import build_router
from src.config import load_config
from src.db import PostRepository
from src.scheduler import PostScheduler
from src.services.publisher import Publisher
from src.services.telegram_publisher import TelegramPublisher
from src.services.vk_publisher import VKPublisher


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    )

    config = load_config()
    bot = Bot(
        token=config.tg_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )

    repo = PostRepository(config.db_path)
    await repo.init()

    tg_publisher = TelegramPublisher(config.tg_target_channels)
    vk_publisher = VKPublisher(
        access_token=config.vk_access_token,
        upload_access_token=config.vk_upload_access_token,
        group_ids=config.vk_group_ids,
        api_version=config.vk_api_version,
    )
    publisher = Publisher(tg_publisher=tg_publisher, vk_publisher=vk_publisher)

    scheduler = PostScheduler(
        repo=repo,
        publisher=publisher,
        bot=bot,
        timezone=config.timezone,
    )
    await scheduler.start_and_restore()

    dp = Dispatcher()
    dp.include_router(build_router(repo=repo, scheduler=scheduler, timezone=config.timezone))

    try:
        await dp.start_polling(bot)
    finally:
        await scheduler.shutdown()
        await repo.close()
        await vk_publisher.close()
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())

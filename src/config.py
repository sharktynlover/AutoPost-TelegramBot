import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


@dataclass(slots=True)
class Config:
    tg_bot_token: str
    tg_target_channels: list[str]
    vk_access_token: str
    vk_upload_access_token: str
    vk_group_ids: list[int]
    vk_api_version: str
    db_path: str
    timezone: ZoneInfo


def _csv(value: str) -> list[str]:
    return [x.strip() for x in value.split(',') if x.strip()]


def load_config() -> Config:
    load_dotenv(encoding='utf-8-sig')

    tg_bot_token = os.getenv('TG_BOT_TOKEN', '').strip()
    if not tg_bot_token:
        raise ValueError('TG_BOT_TOKEN is required')

    tg_target_channels = _csv(os.getenv('TG_TARGET_CHANNELS', ''))
    if not tg_target_channels:
        raise ValueError('TG_TARGET_CHANNELS is required')

    vk_access_token = os.getenv('VK_ACCESS_TOKEN', '').strip()
    if not vk_access_token:
        raise ValueError('VK_ACCESS_TOKEN is required')
    vk_upload_access_token = os.getenv('VK_UPLOAD_ACCESS_TOKEN', '').strip() or vk_access_token

    vk_group_ids_raw = _csv(os.getenv('VK_GROUP_IDS', ''))
    if not vk_group_ids_raw:
        raise ValueError('VK_GROUP_IDS is required')
    vk_group_ids = [int(item) for item in vk_group_ids_raw]

    db_path = os.getenv('DB_PATH', 'autopost.db').strip()
    timezone = ZoneInfo(os.getenv('TIMEZONE', 'Europe/Moscow').strip())

    return Config(
        tg_bot_token=tg_bot_token,
        tg_target_channels=tg_target_channels,
        vk_access_token=vk_access_token,
        vk_upload_access_token=vk_upload_access_token,
        vk_group_ids=vk_group_ids,
        vk_api_version='5.199',
        db_path=db_path,
        timezone=timezone,
    )


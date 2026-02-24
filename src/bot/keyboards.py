from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def target_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='Telegram + VK', callback_data='target:both')
    builder.button(text='Only Telegram', callback_data='target:tg')
    builder.button(text='Only VK', callback_data='target:vk')
    builder.adjust(1)
    return builder.as_markup()

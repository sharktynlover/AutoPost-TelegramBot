from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards import target_keyboard
from src.bot.states import NewPostState
from src.db import PostRepository
from src.scheduler import PostScheduler


def build_router(repo: PostRepository, scheduler: PostScheduler, timezone: ZoneInfo) -> Router:
    router = Router()

    def parse_post_id(message: Message) -> int | None:
        parts = (message.text or '').split(maxsplit=1)
        if len(parts) != 2 or not parts[1].strip().isdigit():
            return None
        return int(parts[1].strip())

    @router.message(Command('start'))
    async def start(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(
            'Команды:\n'
            '/newpost - создать новый пост\n'
            '/list - показать отложенные посты\n'
            '/sendnow <id> - отправить пост досрочно\n'
            '/delete <id> - удалить пост из плана\n\n'
            'Формат времени: `YYYY-MM-DD HH:MM`'
        )

    @router.message(Command('newpost'))
    async def new_post(message: Message, state: FSMContext) -> None:
        await state.clear()
        await state.set_state(NewPostState.waiting_text)
        await message.answer('Отправьте текст поста (Markdown поддерживается).')

    @router.message(Command('list'))
    async def list_posts(message: Message) -> None:
        posts = await repo.list_pending()
        if not posts:
            await message.answer('Нет отложенных постов.')
            return

        lines = []
        for post in posts[:20]:
            targets = []
            if post.send_to_tg:
                targets.append('TG')
            if post.send_to_vk:
                targets.append('VK')
            preview = post.text.replace('\n', ' ')[:40]
            lines.append(
                f"#{post.id} | {post.run_at.astimezone(timezone):%Y-%m-%d %H:%M} | {'+'.join(targets)} | {preview}"
            )
        await message.answer('\n'.join(lines))

    @router.message(Command('sendnow'))
    async def send_now(message: Message) -> None:
        post_id = parse_post_id(message)
        if post_id is None:
            await message.answer('Использование: `/sendnow <id>`')
            return

        _, msg = await scheduler.run_now(post_id)
        await message.answer(msg)

    @router.message(Command('delete'))
    async def delete_post(message: Message) -> None:
        post_id = parse_post_id(message)
        if post_id is None:
            await message.answer('Использование: `/delete <id>`')
            return

        _, msg = await scheduler.cancel(post_id)
        await message.answer(msg)

    @router.message(NewPostState.waiting_text)
    async def got_text(message: Message, state: FSMContext) -> None:
        if not message.text:
            await message.answer('Нужен текст. Попробуйте снова.')
            return
        await state.update_data(text=message.text)
        await state.set_state(NewPostState.waiting_photo)
        await message.answer('Отправьте 1 фото или /skip чтобы пропустить.')

    @router.message(Command('skip'), NewPostState.waiting_photo)
    async def skip_photo(message: Message, state: FSMContext) -> None:
        await state.update_data(photo_file_id=None)
        await state.set_state(NewPostState.waiting_datetime)
        await message.answer('Введите время публикации в формате `YYYY-MM-DD HH:MM`.')

    @router.message(NewPostState.waiting_photo, F.photo)
    async def got_photo(message: Message, state: FSMContext) -> None:
        photo = message.photo[-1]
        await state.update_data(photo_file_id=photo.file_id)
        await state.set_state(NewPostState.waiting_datetime)
        await message.answer('Введите время публикации в формате `YYYY-MM-DD HH:MM`.')

    @router.message(NewPostState.waiting_photo)
    async def wrong_photo(message: Message) -> None:
        await message.answer('Отправьте фото или используйте /skip.')

    @router.message(NewPostState.waiting_datetime)
    async def got_datetime(message: Message, state: FSMContext) -> None:
        raw = (message.text or '').strip()
        try:
            run_at = datetime.strptime(raw, '%Y-%m-%d %H:%M').replace(tzinfo=timezone)
        except ValueError:
            await message.answer('Неверный формат. Нужен `YYYY-MM-DD HH:MM`.')
            return

        if run_at <= datetime.now(timezone):
            await message.answer('Время должно быть в будущем.')
            return

        await state.update_data(run_at=run_at.isoformat())
        await state.set_state(NewPostState.waiting_target)
        await message.answer('Выберите, куда отправлять пост:', reply_markup=target_keyboard())

    @router.callback_query(NewPostState.waiting_target, F.data.startswith('target:'))
    async def got_target(callback: CallbackQuery, state: FSMContext) -> None:
        target = callback.data.split(':', maxsplit=1)[1]
        data = await state.get_data()

        send_to_tg = target in {'tg', 'both'}
        send_to_vk = target in {'vk', 'both'}

        post_id = await repo.create_post(
            text=data['text'],
            photo_file_id=data.get('photo_file_id'),
            run_at=datetime.fromisoformat(data['run_at']),
            send_to_tg=send_to_tg,
            send_to_vk=send_to_vk,
        )
        await scheduler.schedule_post(post_id)

        await state.clear()
        await callback.message.answer(
            f'Пост #{post_id} запланирован.'
        )
        await callback.answer()

    return router

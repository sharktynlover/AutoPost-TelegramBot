from __future__ import annotations

import aiohttp
from aiogram import Bot


class VKPublisher:
    def __init__(
        self,
        access_token: str,
        upload_access_token: str,
        group_ids: list[int],
        api_version: str,
    ) -> None:
        self._access_token = access_token
        self._upload_access_token = upload_access_token
        self._group_ids = group_ids
        self._api_version = api_version
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))

    async def close(self) -> None:
        if not self._session.closed:
            await self._session.close()

    async def publish(self, bot: Bot, text: str, tg_photo_file_id: str | None) -> None:
        for group_id in self._group_ids:
            attachments = None
            if tg_photo_file_id:
                attachments = await self._upload_photo_from_telegram(
                    bot=bot,
                    tg_photo_file_id=tg_photo_file_id,
                    group_id=group_id,
                )

            params = {
                'owner_id': -group_id,
                'from_group': 1,
                'message': text,
            }
            if attachments:
                params['attachments'] = attachments

            await self._api('wall.post', params, token=self._access_token)

    async def _upload_photo_from_telegram(
        self,
        bot: Bot,
        tg_photo_file_id: str,
        group_id: int,
    ) -> str:
        tg_file = await bot.get_file(tg_photo_file_id)
        file_url = f'https://api.telegram.org/file/bot{bot.token}/{tg_file.file_path}'

        async with self._session.get(file_url) as response:
            response.raise_for_status()
            photo_data = await response.read()

        upload_server = await self._api(
            'photos.getWallUploadServer',
            {'group_id': group_id},
            token=self._upload_access_token,
        )
        upload_url = upload_server['upload_url']

        form = aiohttp.FormData()
        form.add_field('photo', photo_data, filename='photo.jpg', content_type='image/jpeg')

        async with self._session.post(upload_url, data=form) as response:
            response.raise_for_status()
            upload_result = await response.json()

        saved = await self._api(
            'photos.saveWallPhoto',
            {
                'group_id': group_id,
                'photo': upload_result['photo'],
                'server': upload_result['server'],
                'hash': upload_result['hash'],
            },
            token=self._upload_access_token,
        )
        photo = saved[0]
        return f"photo{photo['owner_id']}_{photo['id']}"

    async def _api(self, method: str, params: dict, token: str) -> dict:
        payload = {
            **params,
            'access_token': token,
            'v': self._api_version,
        }
        async with self._session.post(f'https://api.vk.com/method/{method}', data=payload) as response:
            response.raise_for_status()
            data = await response.json()

        if 'error' in data:
            error = data['error']
            code = error.get('error_code')
            msg = f"VK API error {code}: {error.get('error_msg')}"
            if code == 27:
                msg += ' | Для фото нужен пользовательский токен в VK_UPLOAD_ACCESS_TOKEN.'
            raise RuntimeError(msg)

        return data['response']

# AutoPost Bot

Telegram-бот для отложенного автопостинга в Telegram-каналы и VK.

## Возможности

- Создание поста через диалог в Telegram
- Отложенная публикация по времени
- Публикация в Telegram, VK или сразу в обе платформы
- Поддержка одного изображения к посту
- Markdown-разметка текста (в Telegram)
- Хранение задач в SQLite

## Структура проекта

```text
autopost/
  app.py
  requirements.txt
  .env.example
  src/
    config.py
    db.py
    models.py
    scheduler.py
    bot/
      handlers.py
      keyboards.py
      states.py
    services/
      publisher.py
      telegram_publisher.py
      vk_publisher.py
```

## Установка

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Настройка окружения

1. Создай файл `.env` на основе шаблона:

```powershell
Copy-Item .env.example .env
```

2. Заполни переменные в `.env`:

```env
TG_BOT_TOKEN=your_telegram_bot_token
TG_TARGET_CHANNELS=@my_channel,-1001234567890
VK_ACCESS_TOKEN=your_vk_group_token
VK_UPLOAD_ACCESS_TOKEN=your_vk_user_token_for_photos
VK_GROUP_IDS=123456789
DB_PATH=autopost.db
TIMEZONE=Europe/Moscow
```

## Переменные окружения

- `TG_BOT_TOKEN` - токен бота из `@BotFather`
- `TG_TARGET_CHANNELS` - список каналов через запятую (`@username` и/или `-100...`)
- `VK_ACCESS_TOKEN` - основной VK токен (обычно токен сообщества) для `wall.post`
- `VK_UPLOAD_ACCESS_TOKEN` - пользовательский VK токен для загрузки фото (`photos.getWallUploadServer`, `photos.saveWallPhoto`)
- `VK_GROUP_IDS` - ID групп VK через запятую, без `club` и без минуса
- `DB_PATH` - путь к SQLite базе
- `TIMEZONE` - таймзона в формате IANA, например `Europe/Moscow` или `Asia/Yekaterinburg`

Если `VK_UPLOAD_ACCESS_TOKEN` не задан, используется `VK_ACCESS_TOKEN`.

## Запуск

```powershell
py -3.12 .\app.py
```

## Команды бота

- `/start` - справка
- `/newpost` - создать новый отложенный пост
- `/list` - список ожидающих публикаций
- `/sendnow <id>` - отправить отложенный пост сразу
- `/delete <id>` - удалить пост из отложенных
- `/skip` - пропустить добавление фото в процессе создания поста

## Подготовка к GitHub

Перед первым пушем:

1. Инициализируй git-репозиторий:

```powershell
git init
git add .
git commit -m "Initial commit"
```

2. Если `.env` уже попадал в индекс, убери его из отслеживания:

```powershell
git rm --cached .env
```

3. Привяжи удалённый репозиторий и отправь код:

```powershell
git branch -M main
git remote add origin https://github.com/<your-user>/<your-repo>.git
git push -u origin main
```

## Важно

- Бот должен быть администратором целевых Telegram-каналов.
- Не указывай один и тот же канал дважды в `TG_TARGET_CHANNELS` (например `@channel` и тот же `-100...`).
- Для постов с фото в VK лучше использовать отдельный пользовательский `VK_UPLOAD_ACCESS_TOKEN`.
- Никогда не публикуй реальный `.env` в открытый репозиторий.

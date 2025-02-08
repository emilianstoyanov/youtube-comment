## YouTube Auto Comment Bot + Telegram Integration

## 📌 **Съдържание**
(Кликнете върху заглавията, за да преминете към съответната секция)

1. [Как работи?](#как-работи)
2. [🛠 Инсталация и настройка](#инсталация-и-настройка)
   - [1️⃣ Клониране на репото](#1️⃣-клониране-на-репото)
   - [3️⃣ Създаване на .env файл с креденшъли](#3️⃣-създаване-на-env-файл-с-креденшъли)
   - [4️⃣ Създаване на база данни (PostgreSQL)](#4️⃣-създаване-на-база-данни-postgresql)
   - [5️⃣ Генериране на YouTube API OAuth 2.0 Client ID](#5️⃣-генериране-на-youtube-api-oauth-20-client-id)
   - [Настройка на Telegram бота](#-настройка-на-telegram-бота)
3. [Команди в Telegram](#команди-в-telegram)
4. [Потенциални грешки и решения](#потенциални-грешки-и-решения)


# 🚀 Автоматизиран YouTube Коментар Бот с Телеграм Контрол

Този бот автоматично коментира на най-новите видеа в избрани от потребителя YouTube канали. Управлението става чрез Telegram бот, където потребителят може да добавя/премахва канали, вижда списък с коментирани видеа и контролира процеса.

📌 Функционалности
✔ Автоматично намира нови видеа от добавени канали
✔ Публикува коментари на най-новото видео от всеки канал
✔ Използва YouTube API v3 (OAuth 2.0) за автентикация
✔ Управление чрез Telegram бот (добавяне/премахване на канали)
✔ Съхранява данни в PostgreSQL (коментирани видеа, потребители, канали)
✔ Запазва коментарите, за да не се повтарят върху едно и също видео
✔ Генерира отчет за коментираните видеа с дата, час, текст на коментара

# 📖 Как работи?

1. Потребителят добавя канал чрез Telegram командата:

```bash
  /add_channel <име> <URL>
```

2. Ботът запазва канала в базата и започва да го следи.

3. На всеки 10 минути проверява за ново видео от добавените канали.

4. Ако намери ново видео, коментира го и записва в базата.

5. Ако потребителят изтрие коментар от YouTube, ботът няма да го публикува отново.
6. Потребителят може да преглежда всички коментирани видеа чрез командата:

```bash
    /already_commented_videos
```

# 🛠 Инсталация и настройка

## 1️⃣ Клониране на репото

```bash
    git clone https://github.com/yourrepo/youtube-comment-bot.git
    cd youtube-comment-bot
```

## 3️⃣ Създаване на .env файл с креденшъли

**Създай .env файл в основната директория:**

```bash
    DATABASE_URL=postgres://user:password@host:port/dbname
    TELEGRAM_TOKEN=your-telegram-bot-token
    GOOGLE_CREDENTIALS='{"installed": {"client_id": "...", "client_secret": "...", "redirect_uris": ["..."]}}'
    YOUTUBE_REFRESH_TOKEN=your-youtube-refresh-token
```

## 4️⃣ Създаване на база данни (PostgreSQL)

```bash
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE NOT NULL,
        username TEXT
    );
    
    CREATE TABLE channels (
        id SERIAL PRIMARY KEY,
        channel_name TEXT NOT NULL,
        channel_url TEXT UNIQUE NOT NULL,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
    );
    
    CREATE TABLE videos (
        id SERIAL PRIMARY KEY,
        channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
        video_id TEXT UNIQUE NOT NULL,
        video_url TEXT NOT NULL,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE posted_comments (
        id SERIAL PRIMARY KEY,
        video_id TEXT REFERENCES videos(video_id) ON DELETE CASCADE,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        comment_text TEXT NOT NULL,
        commented_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
```

## 5️⃣ Генериране на YouTube API OAuth 2.0 Client ID

1. Влез в **Google Cloud Console**
2. Отиди в **API & Services > Credentials**
3. Натисни **Create Credentials > OAuth Client ID**
4. Избери **Desktop App**
5. Изтегли JSON файла и запиши съдържанието му в `.env` като `GOOGLE_CREDENTIALS`

## Настройка на Telegram бота

**Локално стартиране**

```python
    python comment_bot.py
```

**Стартиране на Telegram бота**

```python
    python telegram_bot.py
```

# 📜 Команди в Telegram


| Команда                         | Описание                                        |
|---------------------------------|------------------------------------------------|
| `/start`                        | Приветства потребителя и обяснява функциите на бота |
| `/help`                         | Показва всички команди                         |
| `/add_channel <име> <URL>`      | Добавя YouTube канал за следене               |
| `/list_channels`                | Показва всички добавени канали                 |
| `/remove_channel <Channel ID>`  | Премахва канал от базата                       |
| `/already_commented_videos`     | Листва всички коментирани видеа                |


___________________________________________________________________

# 🔧 Потенциални грешки и решения

| Грешка                                      | Причина                                | Решение |
|---------------------------------------------|----------------------------------------|---------------------------------------------------------------|
| `Request contains an invalid argument.`     | Channel ID не е валиден               | Провери дали `channel_url` е в правилния формат (UC...)       |
| `forbidden (403)`                           | Няма нужните пермишъни                 | Увери се, че OAuth 2.0 има `"youtube.force-ssl"` в `SCOPES`   |
| `quotaExceeded`                             | Достигнат е дневният лимит на API      | Изчакай 24 часа или регистрирай нов API ключ                  |










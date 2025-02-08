## YouTube Auto Comment Bot + Telegram Integration / Автоматизиран YouTube Коментар Бот с Телеграм

🔹 **Ако срещнете проблеми със сетъпа или имате въпроси, можете да се свържете с мен:**

🔹 **If you encounter problems with the setup or have any questions, you can contact me:**  
📧 Email: emilian.stoyanov@outlook.com
---

## 📌 **Contents / Съдържание**

1. [How It Works? / Как работи?](#how-it-works--как-работи)
2. [Installation & Setup / Инсталация и настройка](#installation--setup--инсталация-и-настройка)
    - [1️⃣ Clone the Repository / Клониране на репото](#1️⃣-clone-the-repository--клониране-на-репото)
    - [2️⃣ Create a .env File / Създаване на .env файл](#2️⃣-create-a-env-file--създаване-на-env-файл)
    - [3️⃣ Create the Database (PostgreSQL) / Създаване на база данни (PostgreSQL)](#3️⃣-create-the-database-postgresql--създаване-на-база-данни-postgresql)
    - [4️⃣ Generate YouTube API OAuth 2.0 Client ID / Генериране на YouTube API OAuth 2.0 Client ID](#4️⃣-generate-youtube-api-oauth-20-client-id--генериране-на-youtube-api-oauth-20-client-id)
    - [Telegram Bot Setup / Настройка на Telegram бота](#telegram-bot-setup--настройка-на-telegram-бота)
3. [Telegram Commands / Команди в Telegram](#telegram-commands--команди-в-telegram)
4. [Potential Errors & Solutions / Потенциални грешки и решения](#potential-errors--solutions--потенциални-грешки-и-решения)

---

# 🚀 How It Works? / Как работи?

This bot automatically comments on the latest videos from user-selected YouTube channels. It is managed through a
Telegram bot, allowing users to add/remove channels, view a list of commented videos, and control the process.

Този бот автоматично коментира на най-новите видеа в избрани от потребителя YouTube канали. Управлението става чрез
Telegram бот, където потребителят може да добавя/премахва канали, вижда списък с коментирани видеа и контролира процеса.

### 📌 Features / Функционалности

✔ Automatically finds new videos from added channels / Автоматично намира нови видеа от добавени канали  
✔ Posts comments on the latest video from each channel / Публикува коментари на най-новото видео от всеки канал  
✔ Uses YouTube API v3 (OAuth 2.0) for authentication / Използва YouTube API v3 (OAuth 2.0) за автентикация  
✔ Managed via Telegram bot (add/remove channels) / Управление чрез Telegram бот (добавяне/премахване на канали)  
✔ Stores data in PostgreSQL (commented videos, users, channels) / Съхранява данни в PostgreSQL (коментирани видеа,
потребители, канали)  
✔ Prevents duplicate comments on the same video / Запазва коментарите, за да не се повтарят върху едно и също видео  
✔ Generates a report of commented videos with date, time, and comment text / Генерира отчет за коментираните видеа с
дата, час, текст на коментара

---

# Installation & Setup / Инсталация и настройка

## 1️⃣ Clone the Repository / Клониране на репото

```bash
    git clone https://github.com/yourrepo/youtube-comment-bot.git
    cd youtube-comment-bot
```

## 2️⃣ Create a .env File / Създаване на .env файл

Create a `.env` file in the root directory / Създай `.env` файл в основната директория:

```bash
    DATABASE_URL=postgres://user:password@host:port/dbname
    TELEGRAM_TOKEN=your-telegram-bot-token
    GOOGLE_CREDENTIALS='{"installed": {"client_id": "...", "client_secret": "...", "redirect_uris": ["..."]}}'
    YOUTUBE_REFRESH_TOKEN=your-youtube-refresh-token
```

## 3️⃣ Create the Database (PostgreSQL) / Създаване на база данни (PostgreSQL)

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

## 4️⃣ Generate YouTube API OAuth 2.0 Client ID / Генериране на YouTube API OAuth 2.0 Client ID

1. Go to **Google Cloud Console** / Влез в **Google Cloud Console**
2. Navigate to **API & Services > Credentials** / Отиди в **API & Services > Credentials**
3. Click **Create Credentials > OAuth Client ID** / Натисни **Create Credentials > OAuth Client ID**
4. Select **Desktop App** / Избери **Desktop App**
5. Download the JSON file and save its content in `.env` as `GOOGLE_CREDENTIALS` / Изтегли JSON файла и запиши
   съдържанието му в `.env` като `GOOGLE_CREDENTIALS`

---

# Telegram Commands / Команди в Telegram

| Command / Команда              | Description / Описание                                                                                 |
|--------------------------------|--------------------------------------------------------------------------------------------------------|
| `/start`                       | Greets the user and explains the bot's functions / Приветства потребителя и обяснява функциите на бота |
| `/help`                        | Displays all commands / Показва всички команди                                                         |
| `/add_channel <name> <URL>`    | Adds a YouTube channel for monitoring / Добавя YouTube канал за следене                                |
| `/list_channels`               | Displays all added channels / Показва всички добавени канали                                           |
| `/remove_channel <Channel ID>` | Removes a channel from the database / Премахва канал от базата                                         |
| `/already_commented_videos`    | Lists all commented videos / Листва всички коментирани видеа                                           |

---

# Potential Errors & Solutions / Потенциални грешки и решения

| Error / Грешка                          | Cause / Причина                                             | Solution / Решение                                                                                                   |
|-----------------------------------------|-------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| `Request contains an invalid argument.` | Channel ID is invalid / Channel ID не е валиден             | Check if `channel_url` is in the correct format (UC...) / Провери дали `channel_url` е в правилния формат (UC...)    |
| `forbidden (403)`                       | Missing required permissions / Няма нужните пермишъни       | Ensure OAuth 2.0 has `"youtube.force-ssl"` in `SCOPES` / Увери се, че OAuth 2.0 има `"youtube.force-ssl"` в `SCOPES` |
| `quotaExceeded`                         | API daily limit reached / Достигнат е дневният лимит на API | Wait 24 hours or register a new API key / Изчакай 24 часа или регистрирай нов API ключ                               |

---

## 5️⃣ Deploying the Bot on Heroku / Разгръщане на бота в Heroku

### 1️⃣ **Creating a Heroku Account / Създаване на Heroku акаунт**

If you don't have a Heroku account, create a free one at [Heroku Official Site](https://www.heroku.com/).

Ако нямаш акаунт в Heroku, създай си безплатен от [официалния сайт](https://www.heroku.com/).

### 2️⃣ **Installing Heroku CLI / Инсталиране на Heroku CLI**

If you haven't installed Heroku CLI yet, install it from [here](https://devcenter.heroku.com/articles/heroku-cli).

Ако все още нямаш Heroku CLI, инсталирай го от [тук](https://devcenter.heroku.com/articles/heroku-cli).

Then log in to Heroku:

След това влез в Heroku:

```bash
    heroku login
```

### 3️⃣ **Creating a New Heroku Project / Създаване на нов Heroku проект**

Navigate to your bot's directory:

Отиди в директорията на твоя бот:

```bash
    cd youtube-comment-bot
```

Create a new Heroku project:

Създай нов Heroku проект:

```bash
    heroku create my-youtube-bot
```

(Replace `my-youtube-bot` with a unique name / Замени `my-youtube-bot` с уникално име)

### 4️⃣ **Adding Heroku Git Remote / Добавяне на Heroku Git Remote**

Check if the Heroku remote is added:

Провери дали Heroku remote е добавен:

```bash
    git remote -v
```

If it's not added, add it manually:

Ако не е, добави го ръчно:

```bash
    heroku git:remote -a my-youtube-bot
```

---

## 6️⃣ Setting Up the Database on Heroku / Настройка на база данни в Heroku

Heroku uses PostgreSQL as its database.

Heroku използва PostgreSQL като база данни.

### 1️⃣ **Enabling Heroku Postgres / Активиране на Heroku Postgres**

Run the following command:

Изпълни командата:

```bash
    heroku addons:create heroku-postgresql:hobby-dev
```

This will create a free PostgreSQL database.

Това ще създаде безплатна PostgreSQL база.

### 2️⃣ **Getting the DATABASE_URL / Получаване на DATABASE_URL**

After installing PostgreSQL, run:

След като инсталираш PostgreSQL, изпълни:

```bash
   heroku config
```

You will see the `DATABASE_URL` variable, which contains the database connection string. It will be used to connect to
PostgreSQL.

Ще видиш променлива `DATABASE_URL`, която съдържа връзката към базата. Тя ще се използва за свързване с PostgreSQL.

### 3️⃣ **Creating the Tables / Създаване на таблиците**

Connect to the database and execute the table creation commands:

Свържи се с базата и изпълни командите за създаване на таблиците:

```bash
   heroku pg:psql
```

Then execute:

След което изпълни:

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
       video_title TEXT,
       channel_name TEXT,
       commented_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
```

Exit psql with `\q`.

Излез от psql с `\q`.

---

## 7️⃣ Adding API Keys in Heroku / Добавяне на API ключове в Heroku

Heroku stores sensitive data like API keys and tokens in `config vars`.

Heroku съхранява чувствителни данни като API ключове и токени в `config vars`.

### 1️⃣ **Manually Adding API Keys / Добави API ключовете ръчно**

Run the following commands to save the keys in Heroku:

Изпълни следните команди, за да запазиш ключовете в Heroku:

```bash
   heroku config:set TELEGRAM_TOKEN=your-telegram-bot-token
   heroku config:set TELEGRAM_CHAT_ID=your-telegram-chat-id
   heroku config:set GOOGLE_CREDENTIALS='{"installed": {"client_id": "...", "client_secret": "...", "redirect_uris": ["..."]}}'
   heroku config:set YOUTUBE_REFRESH_TOKEN=your-youtube-refresh-token
```

Replace `your-telegram-bot-token`, `your-telegram-chat-id`, and others with the actual values.

Замени `your-telegram-bot-token`, `your-telegram-chat-id` и останалите с истинските стойности.

---

## 8️⃣ Setting Up Heroku Scheduler / Настройка на Heroku Scheduler

The bot must periodically check for new videos and comment automatically. We use Heroku Scheduler for this.

Ботът трябва да проверява за нови видеа и да коментира автоматично. За това използваме Heroku Scheduler.

### 1️⃣ **Enabling Heroku Scheduler / Активиране на Heroku Scheduler**

Run:

Изпълни:

```bash
  heroku addons:create scheduler:standard
```

Then go to Heroku Dashboard:

След това влез в Heroku Dashboard:

- Open Heroku App > Resources > Heroku Scheduler.
- Click `Add Job` and configure execution:

    - Command: `python comment_bot.py`
    - Schedule: `Every day at 10:30 AM UTC` (or choose another time).

---

## 9️⃣ Deploying the Bot to Heroku / Деплой на бота в Heroku

After setup, it's time to deploy the code.

След като настроим всичко, е време да разположим кода.

### 1️⃣ **Adding Files to Git / Добавяне на файловете в Git**

```bash
  git add .
  git commit -m "Initial commit"
```

### 2️⃣ **Deploying to Heroku / Деплой към Heroku**

```bash
  git push heroku main
```

### 3️⃣ **Starting the Bot / Стартиране на бота**

```bash
  heroku ps:scale worker=1
```

If using a Procfile, ensure it contains:

Ако използваш Procfile, увери се, че съдържа:

```bash
  worker: python comment_bot.py
```

---

## 10️⃣ Logs & Monitoring / Логове и мониторинг

If something isn't working, check the logs:

Ако нещо не работи, провери логовете:

```bash
  heroku logs --tail

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import psycopg2
import os
import re

# Настройка на логове
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Вземи TELEGRAM API Token от @BotFather
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Вземи данни за Postgres
DATABASE_URL = os.getenv("DATABASE_URL")


# Функция за свързване към базата
def connect_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn


# Функция за добавяне на канал
async def add_channel(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ Моля, добавете **име на канала** и **URL на канала**! 📌 Пример: `/add_channel KreteKlizmi https://www.youtube.com/@KreteKlizmi`")
        return

    channel_name = context.args[0]  # Името на канала
    channel_url = context.args[1]  # Линк към канала

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Проверка дали потребителят съществува
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            cursor.execute("INSERT INTO users (telegram_id, username) VALUES (%s, %s) RETURNING id",
                           (user_id, username))
            user_id = cursor.fetchone()[0]
            conn.commit()

        # ✅ Поправена SQL заявка - добавяме channel_name и user_id
        cursor.execute("INSERT INTO channels (channel_name, channel_url, user_id) VALUES (%s, %s, %s)",
                       (channel_name, channel_url, user_id))
        conn.commit()

        cursor.close()
        conn.close()

        await update.message.reply_text(
            f"✅ Каналът **{channel_name}** беше добавен успешно!\n🔗 [Линк към канала]({channel_url})",
            parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        await update.message.reply_text(f"❌ Грешка при добавяне на канала: {e}")


# Функция за добавяне на видео
async def add_video(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ Моля, добавете **URL на видеото** и **URL на канала**! 📌 Пример: `/add_video https://www.youtube.com/watch?v=yszrl5SmFlA https://www.youtube.com/@Example`")
        return

    video_url = context.args[0]
    channel_url = context.args[1]

    # ✅ Извличаме video_id от линка
    video_id_match = re.search(r"v=([a-zA-Z0-9_-]{11})", video_url)
    if not video_id_match:
        await update.message.reply_text(
            "❌ Невалиден YouTube линк! Уверете се, че използвате стандартен формат: `https://www.youtube.com/watch?v=VIDEO_ID`")
        return

    video_id = video_id_match.group(1)  # Взимаме ID-то от URL-а

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Проверка дали потребителят съществува
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            cursor.execute("INSERT INTO users (telegram_id, username) VALUES (%s, %s) RETURNING id",
                           (user_id, username))
            user_id = cursor.fetchone()[0]
            conn.commit()

        # Намери channel_id чрез URL на канала
        cursor.execute("SELECT id FROM channels WHERE channel_url = %s AND user_id = %s", (channel_url, user_id))
        result = cursor.fetchone()

        if result:
            channel_id = result[0]

            # ✅ Вкарваме и video_id в базата
            cursor.execute("""
                INSERT INTO videos (user_id, channel_id, video_url, video_id)
                VALUES (%s, %s, %s, %s)
            """, (user_id, channel_id, video_url, video_id))
            conn.commit()

            await update.message.reply_text(f"🎬 Видео [{video_id}]({video_url}) беше добавено успешно!",
                                            parse_mode="Markdown", disable_web_page_preview=True)
        else:
            await update.message.reply_text("⚠️ Каналът не съществува в базата или не ти принадлежи!")

        cursor.close()
        conn.close()

    except Exception as e:
        await update.message.reply_text(f"❌ Грешка при добавяне на видеото: {e}")


# Функция за показване на всички канали
async def list_channels(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT channel_url FROM channels WHERE user_id = %s", (user_id,))
        channels = cursor.fetchall()

        cursor.close()
        conn.close()

        if not channels:
            await update.message.reply_text("⚠️ Все още нямаш добавени канали.")
            return

        message = "📂 **Твоите канали:**\n\n"
        for index, (url,) in enumerate(channels, start=1):
            message += f"🔹 [{url}]({url})\n"

        await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        await update.message.reply_text(f"❌ Грешка при извличане на каналите: {e}")


async def list_videos(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT video_url FROM videos WHERE user_id = %s", (user_id,))
        videos = cursor.fetchall()

        cursor.close()
        conn.close()

        if not videos:
            await update.message.reply_text("⚠️ Все още нямаш добавени видеа.")
            return

        message = "📜 **Твоите видеа:**\n\n"
        for index, (url,) in enumerate(videos, start=1):
            message += f"🎬 [{url}]({url})\n"

        await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        await update.message.reply_text(f"❌ Грешка при извличане на видеата: {e}")


# Функция за стартиране на бота
async def start(update: Update, context: CallbackContext) -> None:
    user_name = update.message.from_user.first_name
    message = (
        f"👋 **Здравей, {user_name}!**\n\n"
        f"Добре дошъл в YouTube Comment Bot! 🎥\n"
        f"ℹ️ Използвай командата `/help`, за да видиш всички възможности на бота."
    )

    await update.message.reply_text(message, parse_mode="Markdown")


async def help_command(update: Update, context: CallbackContext) -> None:
    message = (
        f"💡 **Команди, които можеш да използваш:**\n\n"

        f"📌 **Добавяне на канал:**\n"
        f"   `/add_channel`  *<име на канала> <URL на канала>*\n\n"

        f"🎬 **Добавяне на видео:**\n"
        f"   `/add_video`  *<URL на видеото> <URL на канала>*\n\n"

        f"📂 **Листване на добавени канали:**\n"
        f"   `/list_channels`\n\n"

        f"📜 **Листване на добавени видеа:**\n"
        f"   `/list_videos`\n\n"

        f"📝 **Добавяне на ключова дума:**\n"
        f"   `/add_keyword`  *<ключова дума>*\n\n"

        f"🔎 **Листване на всички твои ключови думи:**\n"
        f"   `/list_keywords`\n\n"

        f"ℹ️ **Още функции скоро...** 🚀"
    )

    await update.message.reply_text(message, parse_mode="Markdown")


# Функция за добавяне на ключови думи на потребителя
async def add_keyword(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id  # ID на потребителя
    username = update.message.from_user.username  # Telegram username (по избор)

    if len(context.args) < 1:
        await update.message.reply_text("⚠️ Моля, въведи ключова дума! 📌 Пример: `/add_keyword scam`")
        return

    keyword = context.args[0].lower()

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Проверка дали потребителят съществува
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            # Ако потребителят не съществува, го добавяме в `users`
            cursor.execute("INSERT INTO users (telegram_id, username) VALUES (%s, %s) RETURNING id",
                           (user_id, username))
            user_id = cursor.fetchone()[0]
            conn.commit()

        # Добавяне на ключовата дума в `keywords`
        cursor.execute("INSERT INTO keywords (user_id, keyword) VALUES (%s, %s)", (user_id, keyword))
        conn.commit()

        cursor.close()
        conn.close()

        await update.message.reply_text(f"✅ Ключовата дума **'{keyword}'** беше добавена успешно!",
                                        parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Грешка при добавяне на ключовата дума: {e}")


# Функция за листване на добавените ключови думи на потребителя
async def list_keywords(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id  # ID на потребителя

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Взимаме всички ключови думи на потребителя
        cursor.execute("SELECT keyword FROM keywords WHERE user_id = %s", (user_id,))
        keywords = cursor.fetchall()

        cursor.close()
        conn.close()

        if not keywords:
            await update.message.reply_text("⚠️ Все още нямаш добавени ключови думи.")
            return

        message = "🔎 **Твоите ключови думи:**\n\n"
        for index, (keyword,) in enumerate(keywords, start=1):
            message += f"➤ **{index}. {keyword}**\n"

        await update.message.reply_text(message, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Грешка при извличане на ключовите думи: {e}")


# Основна функция за инициализиране на бота
def main() -> None:
    # Използваме новия Application клас за инициализиране на бота
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Добавяне на командите
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_channel", add_channel))
    application.add_handler(CommandHandler("add_video", add_video))
    application.add_handler(CommandHandler("list_channels", list_channels))
    application.add_handler(CommandHandler("list_videos", list_videos))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add_keyword", add_keyword))
    application.add_handler(CommandHandler("list_keywords", list_keywords))

    # Стартиране на бота
    application.run_polling()


if __name__ == '__main__':
    main()

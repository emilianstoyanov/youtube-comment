import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import psycopg2
import os
import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ✅ Настройка на логове
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Вземи TELEGRAM API Token от @BotFather
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ✅ Вземи данни за Postgres
DATABASE_URL = os.getenv("DATABASE_URL")

# ✅ Вземи API ключ за YouTube
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# ✅ Свързваме се с YouTube API
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


def connect_db():
    """Свързване с базата данни"""
    return psycopg2.connect(DATABASE_URL, sslmode='require')


def get_channel_id_from_handle(handle):
    """Конвертира YouTube handle (@Supernaturalee) в истински Channel ID"""
    try:
        request = youtube.channels().list(
            part="id",
            forHandle=handle
        )
        response = request.execute()

        if "items" in response and len(response["items"]) > 0:
            return response["items"][0]["id"]
        else:
            logger.warning(f"⚠️ Не намерихме канал за handle: {handle}")
            return None
    except HttpError as e:
        logger.error(f"❌ Грешка при извличане на Channel ID за handle {handle}: {e}")
        return None


async def add_channel(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ Моля, добавете **име на канала** и **URL на канала**! 📌 Пример: `/add_channel KreteKlizmi https://www.youtube.com/@KreteKlizmi`")
        return

    channel_name = context.args[0]  # Името на канала
    channel_url = context.args[1]  # Линк към канала

    # ✅ Ако каналът е в @handle формат, конвертираме в Channel ID
    if "youtube.com/@" in channel_url:
        handle = channel_url.split("@")[1]  # Взимаме само името след "@"
        channel_id = get_channel_id_from_handle(handle)
    else:
        channel_id = channel_url  # Ако вече е Channel ID

    if not channel_id or not channel_id.startswith("UC"):
        await update.message.reply_text("❌ Неуспешно извличане на Channel ID. Уверете се, че URL е правилен!")
        return

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # ✅ Проверяваме дали потребителят съществува
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            cursor.execute("INSERT INTO users (telegram_id, username) VALUES (%s, %s) RETURNING id",
                           (user_id, username))
            user_id = cursor.fetchone()[0]
            conn.commit()

        # ✅ Добавяме канала с реалното Channel ID
        cursor.execute("INSERT INTO channels (channel_name, channel_url, user_id) VALUES (%s, %s, %s)",
                       (channel_name, channel_id, user_id))
        conn.commit()

        cursor.close()
        conn.close()

        await update.message.reply_text(
            f"✅ Каналът **{channel_name}** беше добавен успешно!\n🔗 Channel ID: `{channel_id}`",
            parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        await update.message.reply_text(f"❌ Грешка при добавяне на канала: {e}")


# ✅ Функцията за добавяне на видео остава същата
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


# ✅ Стартираме бота
def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("add_channel", add_channel))
    application.add_handler(CommandHandler("add_video", add_video))

    application.run_polling()


if __name__ == '__main__':
    main()

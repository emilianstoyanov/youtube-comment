import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import psycopg2
import os
import uuid

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
    if len(context.args) > 1:
        channel_name = context.args[0]
        channel_url = context.args[1]

        try:
            # Свързване към базата
            conn = connect_db()
            cursor = conn.cursor()

            # Добавяне на канала в базата
            cursor.execute("""
                INSERT INTO channels (channel_name, channel_url)
                VALUES (%s, %s)
                RETURNING id
            """, (channel_name, channel_url))
            channel_id = cursor.fetchone()[0]
            conn.commit()

            cursor.close()
            conn.close()

            await update.message.reply_text(f"Каналът {channel_name} ({channel_url}) беше добавен успешно!")
        except Exception as e:
            await update.message.reply_text(f"Грешка при добавяне на канала: {e}")
    else:
        await update.message.reply_text("Моля, добавете име на канала и URL.\n"
                                        "Във фомат: /add_channel human https://www.youtube.com/@human")


async def add_video(update: Update, context: CallbackContext) -> None:
    if len(context.args) > 1:
        video_url = context.args[0]
        channel_url = context.args[1]

        try:
            # Свързване към базата
            conn = connect_db()
            cursor = conn.cursor()

            # Намери channel_id чрез URL на канала
            cursor.execute("SELECT id FROM channels WHERE channel_url = %s", (channel_url,))
            result = cursor.fetchone()

            if result:
                channel_id = result[0]
                # Добавяне на видеото в базата
                # Генерираме уникален video_id (например чрез UUID)
                video_id = str(uuid.uuid4())

                # Добавяне на видеото в базата
                cursor.execute("""
                                   INSERT INTO videos (channel_id, video_url, video_id)
                                   VALUES (%s, %s, %s)
                               """, (channel_id, video_url, video_id))
                conn.commit()

                await update.message.reply_text(f"Видео {video_url} беше добавено успешно!")
            else:
                await update.message.reply_text("Каналът не съществува в базата.")

            cursor.close()
            conn.close()

        except Exception as e:
            await update.message.reply_text(f"Грешка при добавяне на видеото: {e}")
    else:
        await update.message.reply_text("Моля, добавете URL на видеото и на канала.\n"
                                        "Във фомат: /add_video https://www.youtube.com/watch?v=dQwф45х9WgXcQ "
                                        "https://www.youtube.com/@HUMAN")


# Функция за показване на всички канали
async def list_channels(update: Update, context: CallbackContext) -> None:
    try:
        # Свързване към базата
        conn = connect_db()
        cursor = conn.cursor()

        # Извличане на всички канали
        cursor.execute("SELECT channel_name, channel_url FROM channels")
        channels = cursor.fetchall()

        cursor.close()
        conn.close()

        if not channels:
            await update.message.reply_text("❌ Няма добавени канали.")
            return

        # Генериране на съобщението във формат Markdown
        message = "**📌 Добавени канали:**\n\n"
        for index, (name, url) in enumerate(channels, start=1):
            message += f"➤ **{index}. [{name}]({url})**\n"

        await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Грешка при извличане на каналите: {e}")

async def list_videos(update: Update, context: CallbackContext) -> None:
    try:
        # Свързване към базата
        conn = connect_db()
        cursor = conn.cursor()

        # Извличане на всички видеа + името на канала
        cursor.execute("""
            SELECT v.video_url, c.channel_name, c.channel_url 
            FROM videos v
            JOIN channels c ON v.channel_id = c.id
            ORDER BY c.channel_name
        """)
        videos = cursor.fetchall()

        cursor.close()
        conn.close()

        if not videos:
            await update.message.reply_text("❌ Няма добавени видеа.")
            return

        # Генериране на съобщението във формат Markdown
        message = "**🎬 Добавени видеа:**\n\n"
        for index, (video_url, channel_name, channel_url) in enumerate(videos, start=1):
            message += f"➤ **{index}. [Видео]({video_url})** от **[{channel_name}]({channel_url})**\n"

        await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Грешка при извличане на видеата: {e}")


# Функция за стартиране на бота
async def start(update: Update, context: CallbackContext) -> None:
    user_name = update.message.from_user.first_name
    await update.message.reply_text(
        f'Здравей, {user_name}!\n\n'
        f'Използвай следните команди:\n\n'
        f'1. За добавяне на URL на Youtube канал:\n'
        f'   /add_channel <url име на канала> <url на канала> \n\n'

        f'2. За добавяне на URL на видео:\n'
        f'   /add_video <url на видеото> <url на канала> \n\n'

        f'3. За листване на всички добавени канали:\n'
        f'   /list_channels'

        f'4. За листване на всички добавени видеа:\n'
        f'   /list_videos'
    )


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

    # Стартиране на бота
    application.run_polling()


if __name__ == '__main__':
    main()

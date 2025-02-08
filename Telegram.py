import logging
import datetime
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


# def get_channel_id_from_handle(handle):
#     """Конвертира YouTube handle (@Supernaturalee) в истински Channel ID"""
#     try:
#         request = youtube.channels().list(
#             part="id",
#             forHandle=handle
#         )
#         response = request.execute()
#
#         if "items" in response and len(response["items"]) > 0:
#             return response["items"][0]["id"]
#         else:
#             logger.warning(f"⚠️ Не намерихме канал за handle: {handle}")
#             return None
#     except HttpError as e:
#         logger.error(f"❌ Грешка при извличане на Channel ID за handle {handle}: {e}")
#         return None

def get_channel_id_from_handle(handle):
    """Конвертира YouTube handle (@Supernaturalee) в истински Channel ID"""
    try:
        # Премахваме "@" отпред, ако съществува
        handle = handle.lstrip("@")

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


# async def add_channel(update: Update, context: CallbackContext) -> None:
#     """Добавяне на нов YouTube канал"""
#     user_id = update.message.from_user.id
#     username = update.message.from_user.username
#
#     if len(context.args) < 2:
#         await update.message.reply_text(
#             "⚠️ Моля, добавете **име на канала** и **URL на канала**!\n"
#             "📌 Пример: `/add_channel KreteKlizmi https://www.youtube.com/@KreteKlizmi`")
#         return
#
#     channel_name = context.args[0]
#     channel_url = context.args[1]
#
#     if "youtube.com/@" in channel_url:
#         handle = channel_url.split("@")[1]
#         channel_id = get_channel_id_from_handle(handle)
#     else:
#         channel_id = channel_url
#
#     if not channel_id or not channel_id.startswith("UC"):
#         await update.message.reply_text("❌ Неуспешно извличане на Channel ID. Уверете се, че URL е правилен!")
#         return
#
#     try:
#         conn = connect_db()
#         cursor = conn.cursor()
#
#         cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (user_id,))
#         user = cursor.fetchone()
#
#         if not user:
#             cursor.execute("INSERT INTO users (telegram_id, username) VALUES (%s, %s) RETURNING id",
#                            (user_id, username))
#             user_id = cursor.fetchone()[0]
#             conn.commit()
#
#         cursor.execute("INSERT INTO channels (channel_name, channel_url, user_id) VALUES (%s, %s, %s)",
#                        (channel_name, channel_id, user_id))
#         conn.commit()
#
#         cursor.close()
#         conn.close()
#
#         await update.message.reply_text(
#             f"✅ Каналът **{channel_name}** беше добавен успешно!\n🔗 Channel ID: `{channel_id}`",
#             parse_mode="Markdown", disable_web_page_preview=True)
#
#     except Exception as e:
#         await update.message.reply_text(f"❌ Грешка при добавяне на канала: {e}")


async def add_channel(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ Моля, добавете **име на канала** и **URL на канала**! 📌 Пример: `/add_channel KreteKlizmi https://www.youtube.com/@KreteKlizmi`"
        )
        return

    channel_name = context.args[0]  # Името на канала
    channel_url = context.args[1]  # Линк към канала

    # ✅ Ако URL съдържа "@", значи е handle
    if "youtube.com/@" in channel_url:
        handle = channel_url.split("@")[-1]  # Взимаме само handle-а
        channel_id = get_channel_id_from_handle(handle)
    else:
        channel_id = channel_url  # Ако вече е Channel ID

    # ✅ Проверяваме дали channel_id е валиден
    if not channel_id or not channel_id.startswith("UC"):
        await update.message.reply_text("❌ Грешка: Неуспешно извличане на Channel ID. Уверете се, че URL е правилен!")
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
            parse_mode="Markdown", disable_web_page_preview=True
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Грешка при добавяне на канала: {e}")


async def list_channels(update: Update, context: CallbackContext) -> None:
    """📋 Извежда списък с всички добавени канали от потребителя, включително Channel ID за по-лесно управление."""
    user_id = update.message.from_user.id

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # ✅ Взимаме каналите с ID, име, URL и дата на добавяне
        cursor.execute("""
            SELECT channel_name, channel_url, id, created_at 
            FROM channels 
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))

        channels = cursor.fetchall()
        cursor.close()
        conn.close()

        if not channels:
            await update.message.reply_text("⚠️ Все още нямаш добавени канали.")
            return

        # ✅ Подобрено форматиране с ID на канала
        message = "📂 **Твоите YouTube канали:**\n\n"
        for index, (name, channel_id, db_id, created_at) in enumerate(channels, start=1):
            formatted_date = created_at.strftime("%Y-%m-%d %H:%M:%S")  # Форматираме датата
            channel_link = f"https://www.youtube.com/channel/{channel_id}"

            message += (
                f"🔹 **{name}**\n"
                f"   🆔 **ID:** `{channel_id}`\n"
                f"   📅 **Добавен:** `{formatted_date}`\n"
                f"   🔗 [Посети канала]({channel_link})\n"
                f"────────────────────────\n"
            )

        await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        await update.message.reply_text(f"❌ Грешка при извличане на каналите: {e}")


async def remove_channel(update: Update, context: CallbackContext) -> None:
    """❌ Премахва канал от базата по Channel ID"""
    user_id = update.message.from_user.id

    if len(context.args) < 1:
        await update.message.reply_text("⚠️ Моля, въведете **Channel ID** на канала, който искате да премахнете!\n"
                                        "📌 Пример: `/remove_channel UC_x5XG1OV2P6uZZ5FSM9Ttw`")
        return

    channel_id = context.args[0]

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Проверяваме дали потребителят притежава този канал
        cursor.execute("SELECT id FROM channels WHERE channel_url = %s AND user_id = %s", (channel_id, user_id))
        result = cursor.fetchone()

        if not result:
            await update.message.reply_text("⚠️ Каналът не съществува в базата или не ти принадлежи!")
        else:
            cursor.execute("DELETE FROM channels WHERE channel_url = %s AND user_id = %s", (channel_id, user_id))
            conn.commit()
            await update.message.reply_text(f"✅ Каналът с ID `{channel_id}` беше премахнат успешно!",
                                            parse_mode="Markdown")

        cursor.close()
        conn.close()

    except Exception as e:
        await update.message.reply_text(f"❌ Грешка при премахване на канала: {e}")


async def add_video(update: Update, context: CallbackContext) -> None:
    """Добавяне на видео"""
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ Моля, добавете **URL на видеото** и **URL на канала**! 📌 Пример: `/add_video https://www.youtube.com/watch?v=yszrl5SmFlA https://www.youtube.com/@Example`")
        return

    video_url = context.args[0]
    channel_url = context.args[1]

    video_id_match = re.search(r"v=([a-zA-Z0-9_-]{11})", video_url)
    if not video_id_match:
        await update.message.reply_text("❌ Невалиден YouTube линк!")
        return

    video_id = video_id_match.group(1)

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM channels WHERE channel_url = %s AND user_id = %s", (channel_url, user_id))
        result = cursor.fetchone()

        if result:
            channel_id = result[0]
            cursor.execute("INSERT INTO videos (user_id, channel_id, video_url, video_id) VALUES (%s, %s, %s, %s)",
                           (user_id, channel_id, video_url, video_id))
            conn.commit()
            await update.message.reply_text(f"🎬 Видео [{video_id}]({video_url}) беше добавено успешно!",
                                            parse_mode="Markdown", disable_web_page_preview=True)
        else:
            await update.message.reply_text("⚠️ Каналът не съществува в базата или не ти принадлежи!")

        cursor.close()
        conn.close()

    except Exception as e:
        await update.message.reply_text(f"❌ Грешка при добавяне на видеото: {e}")


async def start_command(update: Update, context: CallbackContext) -> None:
    """👋 Приветства потребителя и му дава кратка информация за бота"""
    user_name = update.message.from_user.first_name
    message = (
        f"👋 Здравей, **{user_name}**!\n\n"
        "🎥 **YouTube Auto Comment Bot** е тук, за да ти помогне!\n"
        "✅ Добави YouTube канали и ботът ще публикува автоматични коментари под новите им видеа.\n\n"
        "ℹ️ Използвай `/help`, за да видиш всички налични команди."
    )

    await update.message.reply_text(message, parse_mode="Markdown")


async def help_command(update: Update, context: CallbackContext) -> None:
    """📋 Показва списък с всички налични команди"""
    message = (
        "**💡 Достъпни команди:**\n\n"
        "📌 **Добавяне на канал:**\n"
        "`/add_channel <име на канала> <URL на канала>`\n"
        "_Добавя нов YouTube канал към наблюдаваните._\n\n"

        "📂 **Листване на канали:**\n"
        "`/list_channels`\n"
        "_Показва списък с всички добавени канали._\n\n"

        "❌ **Премахване на канал:**\n"
        "`/remove_channel <Channel ID>`\n"
        "_Премахва даден канал от базата._\n\n"

        "🎬 **Листване на вече коментирани видеа:**\n"
        "`/already_commented_videos`\n"
        "_Показва списък с всички видеа, които ботът вече е коментирал._\n\n"

        "📅 **Филтриране на коментари по дата:**\n"
        "`/comments_from_date <YYYY-MM-DD>`\n"
        "_Показва всички коментари, публикувани на конкретна дата._\n\n"

        "ℹ️ **Още функции ще бъдат добавени скоро... 🚀**"
    )

    await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)


async def already_commented_videos(update: Update, context: CallbackContext) -> None:
    """📜 Показва списък с видеата, на които е оставен коментар."""
    user_id = update.message.from_user.id  # ID на потребителя

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # ✅ Взимаме всички видеа, които вече са коментирани от потребителя
        cursor.execute("""
            SELECT videos.video_url, posted_comments.video_title, posted_comments.channel_name, posted_comments.comment_text, posted_comments.commented_at
            FROM posted_comments
            JOIN videos ON posted_comments.video_id = videos.video_id
            WHERE posted_comments.user_id = %s
            ORDER BY posted_comments.commented_at DESC
            LIMIT 10
        """, (user_id,))

        commented_videos = cursor.fetchall()
        cursor.close()
        conn.close()

        if not commented_videos:
            await update.message.reply_text("⚠️ Все още нямаш коментирани видеа.")
            return

        message = "📜 **Твоите последни коментирани видеа:**\n\n"
        for index, (video_url, video_title, channel_name, comment_text, commented_at) in enumerate(commented_videos,
                                                                                                   start=1):
            message += (
                f"🔹 **Видео {index}:**\n"
                f"🎬 [{video_title}]({video_url}) – 📺 {channel_name}\n"
                f"📅 {commented_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"💬 _{comment_text}_\n\n"
            )

        await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        await update.message.reply_text(f"❌ Грешка при извличане на коментираните видеа: {e}")


async def comments_from_date(update: Update, context: CallbackContext) -> None:
    """📅 Листва коментари само за конкретна дата, като запазва формата от /already_commented_videos"""
    user_id = update.message.from_user.id

    if len(context.args) < 1:
        await update.message.reply_text(
            "⚠️ Моля, въведете дата в правилния формат: `/comments_from_date YYYY-MM-DD`\n"
            "📌 Например: `/comments_from_date 2025-02-08`"
        )
        return

    date_str = context.args[0]

    # ✅ Проверка дали датата е валидна
    try:
        target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        await update.message.reply_text("❌ Грешен формат на датата! Използвайте `/comments_from_date YYYY-MM-DD`.")
        return

    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT videos.video_url, posted_comments.video_title, posted_comments.channel_name, posted_comments.comment_text, posted_comments.commented_at
            FROM posted_comments
            JOIN videos ON posted_comments.video_id = videos.video_id
            WHERE posted_comments.user_id = %s AND DATE(posted_comments.commented_at) = %s
            ORDER BY posted_comments.commented_at DESC
        """, (user_id, target_date))

        comments = cursor.fetchall()
        cursor.close()
        conn.close()

        if not comments:
            await update.message.reply_text(f"ℹ️ Няма коментари за {date_str}.")
            return

        # ✅ Форматираме съобщението
        message = f"📅 **Коментари от {date_str}:**\n\n"
        for video_url, video_title, channel_name, comment_text, commented_at in comments:
            message += (
                f"🎬 **Видео:** [{video_title}]({video_url})\n"
                f"📺 **Канал:** {channel_name}\n"
                f"💬 **Коментар:** {comment_text}\n"
                f"🕒 **Дата и час:** {commented_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"────────────────────────\n"
            )

        await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        await update.message.reply_text(f"❌ Грешка при извличане на коментарите: {e}")


def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add_channel", add_channel))
    application.add_handler(CommandHandler("list_channels", list_channels))
    application.add_handler(CommandHandler("remove_channel", remove_channel))
    application.add_handler(CommandHandler("already_commented_videos", already_commented_videos))
    application.add_handler(CommandHandler("comments_from_date", comments_from_date))
    # application.add_handler(CommandHandler("add_video", add_video))

    application.run_polling()


if __name__ == '__main__':
    main()

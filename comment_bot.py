import os
import json
import psycopg2
import random
import googleapiclient.discovery
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import logging
from dotenv import load_dotenv

# ✅ Логове за дебъгване
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ✅ Зареждаме променливите от .env файла
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN")

if not DATABASE_URL:
    raise ValueError("❌ Грешка: DATABASE_URL не е зададен!")
if not GOOGLE_CREDENTIALS:
    raise ValueError("❌ Грешка: GOOGLE_CREDENTIALS не е зададен!")

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]


def get_authenticated_service():
    """Свързване с YouTube API чрез OAuth 2.0 (без нужда от ръчно влизане)"""
    creds = None
    credentials_json = json.loads(GOOGLE_CREDENTIALS)

    if REFRESH_TOKEN:
        creds = Credentials.from_authorized_user_info({
            "token": None,
            "refresh_token": REFRESH_TOKEN,
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": credentials_json["installed"]["client_id"],
            "client_secret": credentials_json["installed"]["client_secret"]
        })
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_config(credentials_json, SCOPES)
        creds = flow.run_console()
        logger.info("🔑 Нов OAuth токен генериран. Запази refresh_token за бъдеща употреба!")

    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)


# ✅ Свързваме се с YouTube API чрез OAuth
youtube = get_authenticated_service()


def connect_db():
    """Свързване към PostgreSQL"""
    return psycopg2.connect(DATABASE_URL, sslmode='require')


def fetch_latest_video_for_channel(channel_id):
    """Взема най-новото видео от даден YouTube канал"""
    try:
        logger.info(f"🔍 Извличаме последното видео от канал (channel_id): {channel_id}...")

        if not channel_id.startswith("UC"):
            logger.error(f"❌ Грешен Channel ID: {channel_id}. Очакваме ID да започва с 'UC'.")
            return None, None

        request = youtube.search().list(
            part="id",
            channelId=channel_id,  # Подаваме channel_url, който вече е Channel ID
            order="date",
            maxResults=1
        )

        response = request.execute()
        logger.info(f"📩 Отговор от YouTube API: {response}")

        if "items" in response and len(response["items"]) > 0:
            video_data = response["items"][0]

            if "videoId" in video_data["id"]:
                video_id = video_data["id"]["videoId"]
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"✅ Намерено видео: {video_url}")
                return video_id, video_url
            else:
                logger.warning("⚠️ Няма videoId в отговора.")
                return None, None
        else:
            logger.warning(f"⚠️ Няма намерени видеа за канал {channel_id}.")
            return None, None

    except Exception as e:
        logger.error(f"❌ Грешка при извличане на видео за канал {channel_id}: {e}")
        return None, None


def add_video_to_db(video_id, video_url, channel_id, user_id):
    """Добавя ново видео в базата, ако още не съществува"""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM videos WHERE video_id = %s", (video_id,))
    exists = cursor.fetchone()[0]
    if exists == 0:
        cursor.execute("""
            INSERT INTO videos (channel_id, video_url, video_id, user_id)
            VALUES (%s, %s, %s, %s)
        """, (channel_id, video_url, video_id, user_id))
        conn.commit()
        logger.info(f"✅ Видео добавено в базата: {video_url}")
    cursor.close()
    conn.close()


def get_channels_from_db():
    """Взима всички канали и потребителите им от базата"""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, channel_url, user_id FROM channels")
    channels = cursor.fetchall()
    cursor.close()
    conn.close()
    return channels


def get_latest_videos():
    """Взема новите видеа от базата, които още не са коментирани"""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT videos.video_id, videos.video_url, videos.channel_id, channels.user_id
        FROM videos
        JOIN channels ON videos.channel_id = channels.id
        WHERE videos.video_id NOT IN (SELECT video_id FROM posted_comments)
    """)
    videos = cursor.fetchall()
    cursor.close()
    conn.close()
    return videos


def has_already_commented(video_id, user_id):
    """Проверява дали вече сме коментирали дадено видео"""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM posted_comments WHERE video_id = %s AND user_id = %s", (video_id, user_id))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count > 0


def post_comment(youtube, video_id, comment_text):
    """Публикува коментар в YouTube"""
    try:
        request = youtube.commentThreads().insert(
            part="snippet",
            body={"snippet": {"videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": comment_text}}}}
        )
        request.execute()
        logger.info(f"✅ Коментар публикуван на {video_id}")
    except HttpError as e:
        logger.error(f"❌ Грешка при публикуване: {e}")


def save_posted_comment(video_id, user_id, comment_text):
    """Запазва коментара в `posted_comments`, за да не се публикува отново."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO posted_comments (video_id, user_id, comment_text)
        VALUES (%s, %s, %s)
    """, (video_id, user_id, comment_text))

    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"💾 Запазен коментар в базата за видео {video_id}")


def run_comment_bot():
    """Основна логика на бота"""
    channels = get_channels_from_db()

    for channel_url, user_id in channels:  # ✅ Взимаме channel_url вместо channel_id
        logger.info(f"🔍 Проверяваме за нови видеа в канал {channel_url}...")

        video_id, video_url = fetch_latest_video_for_channel(channel_url)  # ✅ подаваме `channel_url`

        if video_id:
            add_video_to_db(video_id, video_url, channel_url, user_id)  # ✅ подаваме `channel_url`

    videos = get_latest_videos()

    if not videos:
        logger.info("🚫 Няма нови видеа за коментиране.")
        return

    for video_id, video_url, channel_id, user_id in videos:
        # ✅ Добавяме `user_id`, за да съответства на `has_already_commented(video_id, user_id)`
        if has_already_commented(video_id, user_id):
            logger.info(f"🚫 Пропускаме {video_url}, защото вече сме коментирали.")
            continue  # 🚀 Ако вече е коментирано, пропускаме

        comments = ["Страхотно видео! 🔥", "Браво, много добро съдържание! 👌", "Този контент е супер полезен! 🚀"]
        comment_text = random.choice(comments)

        if post_comment(youtube, video_id, comment_text):
            logger.info(f"✅ Коментар публикуван: {comment_text} на {video_url}")
            save_posted_comment(video_id, user_id, comment_text)  # ✅ Запазваме в базата


if __name__ == "__main__":
    run_comment_bot()

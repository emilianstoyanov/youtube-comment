import os
import psycopg2
from googleapiclient.discovery import build
import json
from dotenv import load_dotenv
from telegram import Bot
import asyncio
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Зареждаме променливите от .env файла
load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# 🔹 Свързваме се с YouTube API
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# 🔹 Връзка към PostgreSQL базата (Heroku)
DATABASE_URL = os.getenv("DATABASE_URL")


def connect_db():
    return psycopg2.connect(DATABASE_URL, sslmode='require')


def get_videos_and_keywords(user_id):
    """Взима всички видеа и ключови думи на конкретния потребител."""
    conn = connect_db()
    cursor = conn.cursor()

    # 🔹 Извличаме видеата на потребителя
    cursor.execute("SELECT video_id, video_url FROM videos WHERE user_id = %s", (user_id,))
    videos = cursor.fetchall()

    # 🔹 Извличаме ключовите думи на потребителя
    cursor.execute("SELECT keyword FROM keywords WHERE user_id = %s", (user_id,))
    keywords = [row[0].lower() for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return videos, keywords


def get_video_comments(video_id):
    """Взима коментарите от дадено видео в YouTube."""
    try:
        comments = []
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            textFormat="plainText",
            maxResults=50  # 🔹 Взимаме до 50 коментара (може да се увеличи)
        )
        response = request.execute()

        for item in response.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "author": comment["authorDisplayName"],
                "text": comment["textDisplay"],
                "published_at": comment["publishedAt"]
            })

        return comments

    except Exception as e:
        print(f"❌ Грешка при извличане на коментари за {video_id}: {e}")
        return []


def analyze_comments(comments, keywords):
    """Анализира коментарите и връща само тези, които съдържат ключови думи + настроението им."""
    matched_comments = []

    for comment in comments:
        sentiment = analyze_sentiment(comment["text"])  # AI анализ на настроението

        for keyword in keywords:
            if keyword in comment["text"].lower():
                matched_comments.append({
                    "author": comment["author"],
                    "text": comment["text"],
                    "sentiment": sentiment,  # 🔥 Добавяме настроението
                    "published_at": comment["published_at"]
                })
                break

    return matched_comments


# Основна функция – изпълнява целия процес
def run_comment_analysis(user_id):
    """Основна функция за извличане и анализ на коментари за потребителя."""
    videos, keywords = get_videos_and_keywords(user_id)
    report = []

    for video_id, video_url in videos:
        comments = get_video_comments(video_id)
        matched_comments = analyze_comments(comments, keywords)

        if matched_comments:
            report.append({
                "video_url": video_url,
                "video_id": video_id,
                "matched_comments": matched_comments
            })

    return report


# Изпращане на резултата в JSON файл
def save_report(user_id, report):
    """Запазва резултата в JSON файл."""
    file_path = f"C:\\Users\\lenovo\\Desktop\\Comments\\report_{user_id}.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    return file_path


def run_comment_analysis(user_id):
    """Основна функция за анализ на коментари."""
    videos, keywords = get_videos_and_keywords(user_id)
    print(f"📌 Проверяваме {len(videos)} видеа за {len(keywords)} ключови думи.")

    report = []
    for video_id, video_url in videos:
        print(f"🔍 Сканираме видео: {video_url} ({video_id})")
        comments = get_video_comments(video_id)
        print(f"   - Намерени {len(comments)} коментара.")

        matched_comments = analyze_comments(comments, keywords)
        print(f"   ✅ {len(matched_comments)} съвпадащи коментара!")

        if matched_comments:
            report.append({
                "video_url": video_url,
                "video_id": video_id,
                "matched_comments": matched_comments
            })

    return report


# Вземаме Telegram API Token и инициализираме бота
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TELEGRAM_TOKEN)


async def send_report_to_telegram(user_id, file_path, summary):
    """Изпраща JSON файла и текстов отчет в Telegram."""
    try:
        # 📄 Изпращаме файла
        with open(file_path, "rb") as file:
            await bot.send_document(chat_id=user_id, document=file, caption="📄 Ето твоя отчет за коментарите!")

        # 📌 Изпращаме резюме
        await bot.send_message(chat_id=user_id, text=summary, parse_mode="Markdown", disable_web_page_preview=True)

        print(f"✅ Файлът и отчетът бяха изпратени успешно на потребителя {user_id}.")
    except Exception as e:
        print(f"❌ Грешка при изпращане на файла: {e}")


def get_current_date():
    """Връща днешната дата във формат: 6 Февруари 2025"""
    months = {
        1: "Януари", 2: "Февруари", 3: "Март", 4: "Април",
        5: "Май", 6: "Юни", 7: "Юли", 8: "Август",
        9: "Септември", 10: "Октомври", 11: "Ноември", 12: "Декември"
    }
    now = datetime.now()
    return f"{now.day} {months[now.month]} {now.year}"


# Инициализираме анализатора
analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(comment):
    """Анализира настроението на коментар: позитивно, негативно или неутрално."""
    sentiment_score = analyzer.polarity_scores(comment)["compound"]

    if sentiment_score >= 0.05:
        return "😊 Позитивно"
    elif sentiment_score <= -0.05:
        return "😠 Негативно"
    else:
        return "😐 Неутрално"


def generate_report_summary(report):
    """Генерира кратък текстов отчет за анализираните видеа + статистика на настроенията."""
    current_date = get_current_date()
    summary = f"📅 **Отчет за {current_date}**\n\n"
    summary += f"📌 Проверени видеа: {len(report)}\n\n"

    total_positive = 0
    total_negative = 0
    total_neutral = 0

    for entry in report:
        video_url = entry["video_url"]
        video_id = entry["video_id"]
        total_comments = len(entry["matched_comments"])

        # 🔹 Анализираме настроението на коментарите
        positive = sum(1 for c in entry["matched_comments"] if c["sentiment"] == "😊 Позитивно")
        negative = sum(1 for c in entry["matched_comments"] if c["sentiment"] == "😠 Негативно")
        neutral = total_comments - (positive + negative)

        total_positive += positive
        total_negative += negative
        total_neutral += neutral

        summary += f"🔍 **Видео:** [{video_id}]({video_url})\n"
        summary += f"   - 📢 **Общо коментари:** {total_comments}\n"
        summary += f"   ✅ **Съвпадащи коментари:** {total_comments}\n"
        summary += f"   - 😊 **Позитивни:** {positive}\n"
        summary += f"   - 😠 **Негативни:** {negative}\n"
        summary += f"   - 😐 **Неутрални:** {neutral}\n\n"

    # 🔹 Обща статистика
    summary += "📊 **Обща статистика на настроенията:**\n"
    summary += f"   - 😊 **Позитивни:** {total_positive}\n"
    summary += f"   - 😠 **Негативни:** {total_negative}\n"
    summary += f"   - 😐 **Неутрални:** {total_neutral}\n"

    return summary


if __name__ == "__main__":
    user_id = 1918226470  # 🔹 Реален Telegram ID
    report = run_comment_analysis(user_id)

    if report:
        file_path = save_report(user_id, report)  # 🔹 Запазваме JSON файла
        summary = generate_report_summary(report)  # 🔹 Генерираме отчет

        asyncio.run(send_report_to_telegram(user_id, file_path, summary))  # 🔹 Изпращаме файла и отчета
    else:
        print("🚫 Няма съвпадащи коментари.")

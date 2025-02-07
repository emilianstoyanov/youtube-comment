import psycopg2
import os

# Свързване с базата данни
DATABASE_URL = os.environ.get("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Създаване на таблица за канали
cursor.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        id SERIAL PRIMARY KEY,
        channel_name VARCHAR(255) NOT NULL,
        channel_url VARCHAR(255) NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Създаване на таблица за видеа
cursor.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        id SERIAL PRIMARY KEY,
        channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
        video_url VARCHAR(255) NOT NULL,
        video_id VARCHAR(255) NOT NULL UNIQUE,
        title VARCHAR(255),
        published_at TIMESTAMP
    )
""")

# ✅ Първо създаваме таблицата `users`, ако не съществува
cursor.execute("""
     CREATE TABLE IF NOT EXISTS users (
         id SERIAL PRIMARY KEY,
         telegram_id BIGINT UNIQUE NOT NULL,
         username VARCHAR(255)
     )
 """)

# ✅ След това създаваме `keywords`, която зависи от `users`
cursor.execute("""
     CREATE TABLE IF NOT EXISTS keywords (
         id SERIAL PRIMARY KEY,
         user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
         keyword VARCHAR(255) NOT NULL,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
     )
 """)

cursor.execute("""
       CREATE TABLE IF NOT EXISTS posted_comments (
           id SERIAL PRIMARY KEY,
           video_id VARCHAR(255) NOT NULL,
           user_id BIGINT NOT NULL,
           comment_text TEXT NOT NULL,
           timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
       );
   """)

# Потвърждаваме промените
conn.commit()

print("Таблиците бяха създадени успешно!")

# Затваряме връзката
cursor.close()
conn.close()

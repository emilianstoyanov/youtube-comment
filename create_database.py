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

# Потвърждаваме промените
conn.commit()

print("Таблиците бяха създадени успешно!")

# Затваряме връзката
cursor.close()
conn.close()

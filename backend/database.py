import sqlite3
from pathlib import Path


DATABASE_NAME = Path(__file__).resolve().parent / "news.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row

    connection.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            content TEXT,
            source TEXT,
            url TEXT UNIQUE,
            image TEXT,
            published_at TEXT,
            relevance_score INTEGER DEFAULT 0
        )
    """)

    connection.commit()

    return connection


def create_table():
    connection = get_connection()
    connection.close()

    print("News database and table created successfully!")


def get_latest_news(limit=10):
    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM news
        ORDER BY published_at DESC
        LIMIT ?
    """, (limit,)).fetchall()

    connection.close()

    return [dict(row) for row in rows]


if __name__ == "__main__":
    create_table()


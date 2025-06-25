import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "movies.db")

# Initialize the database


def setup_database():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                image_url TEXT
            )
        """)
    print("Database initialized successfully.")


if __name__ == "__main__":
    setup_database()

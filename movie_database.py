import psycopg2
import os
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("PGDATABASE"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD"),
    "host": os.getenv("PGHOST"),
    "port": os.getenv("PGPORT"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def setup_database():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movies (
                    id SERIAL PRIMARY KEY,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    year TEXT NOT NULL,
                    image_url TEXT
                )
            """)
        conn.commit()
    print("PostgreSQL database initialized successfully.")


if __name__ == "__main__":
    setup_database()

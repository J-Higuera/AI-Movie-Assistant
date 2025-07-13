from flask import Flask, request, jsonify
import os
import requests
from urllib.parse import quote
import psycopg2
from dotenv import load_dotenv
from flask_cors import CORS


load_dotenv()


def get_connection():
    return psycopg2.connect(os.getenv("${{Postgres.DATABASE_URL}}"))


app = Flask(__name__)
CORS(app)

CORS(app, origins=["http://localhost:5173",
     "https://juanh-portfolio.netlify.app"])

# DB connection config
DB_CONFIG = {
    "dbname": os.getenv("PGDATABASE"),
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD"),
    "host": os.getenv("PGHOST"),
    "port": os.getenv("PGPORT"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def init_db():
    with get_connection() as conn:
        with conn.cursor() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS movies (
                    id SERIAL PRIMARY KEY,
                    category TEXT NOT NULL,
                    title TEXT UNIQUE NOT NULL,
                    year TEXT NOT NULL,
                    image_url TEXT
                )
            """)
        conn.commit()
    print("✅ PostgreSQL DB initialized")


@app.route('/ping')
def ping():
    return jsonify({"status": "ok"})


@app.route('/')
def home():
    return "🎬 Movie Assistant PostgreSQL backend is live!"


@app.route('/add_movie', methods=['POST', 'OPTIONS'])
def add_movie():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json()
    category = data.get('category', '').strip().lower()
    title_input = data.get('title', '').strip()
    year = data.get('year', '').strip()

    if not category or not title_input:
        return jsonify({"message": "Category and title are required."}), 400

    image_url = ""
    api_key = "b7ae81cc"

    try:
        # Search OMDb to find accurate title + year
        search_url = f"http://www.omdbapi.com/?s={quote(title_input)}&y={year}&apikey={api_key}"
        search_data = requests.get(search_url).json()

        accurate_title = title_input
        if search_data.get("Search"):
            best_match = search_data["Search"][0]
            accurate_title = best_match["Title"]
            year = best_match["Year"]

        # Fetch poster
        movie_url = f"http://www.omdbapi.com/?t={quote(accurate_title)}&y={year}&apikey={api_key}"
        result = requests.get(movie_url).json()
        poster = result.get("Poster")

        if poster and poster != "N/A":
            image_url = poster

    except Exception as e:
        print(f"OMDb fetch error: {e}")

    try:
        with get_connection() as conn:
            with conn.cursor() as c:
                c.execute(
                    "SELECT 1 FROM movies WHERE LOWER(title) = LOWER(%s)", (title_input,))
                if c.fetchone():
                    return jsonify({"message": "Movie already exists."}), 409

                c.execute(
                    "INSERT INTO movies (category, title, year, image_url) VALUES (%s, %s, %s, %s)",
                    (category, title_input, year, image_url)
                )
                conn.commit()
        return jsonify({"message": "✅ Movie added!"})
    except Exception as e:
        return jsonify({"message": f"Database error: {str(e)}"}), 500


@app.route('/get_movies/<category>', methods=['GET', 'OPTIONS'])
def get_movies(category):
    if request.method == 'OPTIONS':
        return '', 204

    category = category.strip().lower()
    try:
        with get_connection() as conn:
            with conn.cursor() as c:
                c.execute(
                    "SELECT title, image_url FROM movies WHERE category = %s", (
                        category,)
                )
                results = c.fetchall()
                movies = [{"title": row[0], "image_url": row[1]}
                          for row in results]
        return jsonify({"movies": movies})
    except Exception as e:
        return jsonify({"message": f"Fetch error: {str(e)}"}), 500


@app.route('/delete_movie', methods=['POST', 'OPTIONS'])
def delete_movie():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json()
    category = data.get('category', '').strip().lower()
    title = data.get('title', '').strip()

    if not category:
        return jsonify({"message": "Category is required."}), 400

    try:
        with get_connection() as conn:
            with conn.cursor() as c:
                if title:
                    c.execute(
                        "DELETE FROM movies WHERE category = %s AND LOWER(title) = LOWER(%s)", (category, title))
                else:
                    c.execute(
                        "DELETE FROM movies WHERE category = %s", (category,))
                conn.commit()
        return jsonify({"message": "✅ Movie(s) deleted."})
    except Exception as e:
        return jsonify({"message": f"Delete error: {str(e)}"}), 500


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

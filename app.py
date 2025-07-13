from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sqlite3
import requests
from urllib.parse import quote, quote_plus

app = Flask(__name__)
CORS(app)  # Allow all origins for now

DATABASE = 'movies.db'


def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS movies (
                        id INTEGER PRIMARY KEY,
                        category TEXT,
                        title TEXT UNIQUE,
                        image_url TEXT
                    )''')
        conn.commit()


@app.route('/ping')
def ping():
    return jsonify({"status": "ok"})


@app.route('/')
def home():
    return "🎬 Movie Database backend is running!"


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
    api_key = "b7ae81cc"  # Replace with your own OMDb key

    try:
        # Search OMDb for accurate title/year
        search_url = f"http://www.omdbapi.com/?s={quote(title_input)}&y={year}&apikey={api_key}"
        search_response = requests.get(search_url)
        search_data = search_response.json()

        accurate_title = title_input
        if search_data.get("Search"):
            best_match = search_data["Search"][0]
            accurate_title = best_match["Title"]
            year = best_match["Year"]

        # Fetch full movie details
        movie_url = f"http://www.omdbapi.com/?t={quote(accurate_title)}&y={year}&apikey={api_key}"
        movie_response = requests.get(movie_url)
        result = movie_response.json()

        # Store OMDb image URL directly (no local saving)
        if result.get("Poster") and result["Poster"] != "N/A":
            image_url = result["Poster"]

    except Exception as e:
        print(f"Error fetching poster: {e}")

    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT 1 FROM movies WHERE LOWER(title) = LOWER(?)", (title_input,))
            if c.fetchone():
                return jsonify({"message": "Movie already exists."}), 409

            c.execute("INSERT INTO movies (category, title, image_url) VALUES (?, ?, ?)",
                      (category, title_input, image_url))
            conn.commit()
        return jsonify({"message": "✅ Movie added!"})
    except Exception as e:
        return jsonify({"message": f"Database error: {str(e)}"}), 500


@app.route('/get_movies/<category>', methods=['GET', 'OPTIONS'])
def get_movies(category):
    if request.method == 'OPTIONS':
        return '', 204

    category = category.strip().lower()
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT title, image_url FROM movies WHERE category = ?", (category,))
        results = c.fetchall()
        movies = [{"title": row[0], "image_url": row[1]} for row in results]

    return jsonify({"movies": movies})


@app.route('/delete_movie', methods=['POST', 'OPTIONS'])
def delete_movie():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json()
    category = data.get('category', '').strip().lower()
    title = data.get('title', '').strip()

    if not category:
        return jsonify({"message": "Category is required."}), 400

    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        if title:
            c.execute(
                "DELETE FROM movies WHERE category = ? AND LOWER(title) = LOWER(?)", (category, title))
        else:
            c.execute("DELETE FROM movies WHERE category = ?", (category,))
        conn.commit()

    return jsonify({"message": "✅ Movie(s) deleted."})


@app.route('/images/movie images/<filename>')
def serve_movie_image(filename):
    return send_from_directory('images/movie images', filename)


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

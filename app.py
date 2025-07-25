from flask import Flask, request, redirect, render_template, jsonify
import sqlite3
import string
import random
import os

app = Flask(__name__)
DB_NAME = 'database.db'

# Initialize DB
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS url_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            long_url TEXT NOT NULL UNIQUE,
            short_url TEXT NOT NULL UNIQUE,
            clicks INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Generate short code
def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

# DB connection
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Handle form submission
@app.route('/shorten', methods=['POST'])
def shorten_url():
    long_url = request.form['long_url'].strip()
    conn = get_db_connection()

    # Check if already exists
    row = conn.execute('SELECT short_url FROM url_mapping WHERE long_url = ?', (long_url,)).fetchone()
    if row:
        short_code = row['short_url']
    else:
        short_code = generate_short_code()
        conn.execute(
            'INSERT INTO url_mapping (long_url, short_url, clicks) VALUES (?, ?, ?)',
            (long_url, short_code, 0)
        )
        conn.commit()

    conn.close()
    short_link = f"/{short_code}"  # relative path
    return f"Short URL: <a href='{short_link}' target='_blank'>{request.host_url}{short_code}</a>"

# Redirect short URL
@app.route('/<short_code>')
def redirect_url(short_code):
    conn = get_db_connection()
    row = conn.execute('SELECT long_url, clicks FROM url_mapping WHERE short_url = ?', (short_code,)).fetchone()

    if row:
        # Update click count
        conn.execute('UPDATE url_mapping SET clicks = clicks + 1 WHERE short_url = ?', (short_code,))
        conn.commit()
        conn.close()
        return redirect(row['long_url'])
    else:
        conn.close()
        return 'Invalid or expired short URL.', 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

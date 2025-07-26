from flask import Flask, request, redirect, render_template, jsonify
import os
import string
import random
import psycopg2
from urllib.parse import urlparse

app = Flask(__name__)

# Function to connect to PostgreSQL using DATABASE_URL
def get_db_connection():
    result = urlparse(os.environ['DATABASE_URL'])
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port

    conn = psycopg2.connect(
        dbname=database,
        user=username,
        password=password,
        host=hostname,
        port=port
    )
    return conn

# One-time DB setup function
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS url_mapping (
            id SERIAL PRIMARY KEY,
            long_url TEXT UNIQUE NOT NULL,
            short_url TEXT UNIQUE NOT NULL,
            clicks INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Generate random short code
def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

# Home page route
@app.route('/')
def index():
    return render_template('index.html')

# Handle form submission
@app.route('/shorten', methods=['POST'])
def shorten_url():
    long_url = request.form['long_url'].strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if URL already exists
    cursor.execute('SELECT short_url FROM url_mapping WHERE long_url = %s', (long_url,))
    row = cursor.fetchone()

    if row:
        short_code = row[0]
    else:
        short_code = generate_short_code()
        cursor.execute(
            'INSERT INTO url_mapping (long_url, short_url) VALUES (%s, %s)',
            (long_url, short_code)
        )
        conn.commit()

    conn.close()
    # Return custom short domain
    short_link = f"https://chan/{short_code}"  # or use request.host_url if not using custom domain
    return f"Short URL: <a href='/{short_code}' target='_blank'>{short_link}</a>"

# Redirect from short URL to original long URL
@app.route('/<short_code>')
def redirect_url(short_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT long_url FROM url_mapping WHERE short_url = %s', (short_code,))
    row = cursor.fetchone()

    if row:
        long_url = row[0]
        # Update click count
        cursor.execute('UPDATE url_mapping SET clicks = clicks + 1 WHERE short_url = %s', (short_code,))
        conn.commit()
        conn.close()
        return redirect(long_url)
    else:
        conn.close()
        return "Invalid or expired short URL", 404

# Only run once locally to set up DB (skip during render deployment)
if __name__ == '__main__':
    if os.environ.get("RUN_DB_INIT", "false") == "true":
        init_db()

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

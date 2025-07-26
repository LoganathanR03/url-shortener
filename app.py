from flask import Flask, request, redirect, render_template
import psycopg
import string
import random
import os

app = Flask(__name__)

# Get DATABASE_URL from environment variables (Render) or use fallback
DATABASE_URL = os.environ.get("DATABASE_URL") or "postgresql://tc_user:G73AhzPO8ZfroiXUejJgH1iXMciRfPQn@dpg-d22553be5dus7399csp0-a.singapore-postgres.render.com/tc_db_qu7e"

# Initialize DB
def init_db():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS url_mapping (
                    id SERIAL PRIMARY KEY,
                    long_url TEXT NOT NULL UNIQUE,
                    short_code TEXT NOT NULL UNIQUE,
                    clicks INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            conn.commit()

# Generate short code
def generate_short_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Handle form submission
@app.route('/shorten', methods=['POST'])
def shorten_url():
    long_url = request.form['long_url'].strip()

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT short_code FROM url_mapping WHERE long_url = %s", (long_url,))
            result = cur.fetchone()

            if result:
                short_code = result[0]
            else:
                short_code = generate_short_code()
                cur.execute("INSERT INTO url_mapping (long_url, short_code) VALUES (%s, %s)", (long_url, short_code))
                conn.commit()

    full_short_url = f"https://chan/{short_code}"  # Custom domain/tag
    return f"Short URL: <a href='/{short_code}' target='_blank'>{full_short_url}</a>"

# Redirect short URL
@app.route('/<short_code>')
def redirect_url(short_code):
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT long_url FROM url_mapping WHERE short_code = %s", (short_code,))
            result = cur.fetchone()

            if result:
                long_url = result[0]
                cur.execute("UPDATE url_mapping SET clicks = clicks + 1 WHERE short_code = %s", (short_code,))
                conn.commit()
                return redirect(long_url)
            else:
                return "Invalid or expired short URL.", 404

if __name__ == '__main__':
    init_db()  # <-- Moved this here
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

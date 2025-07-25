from flask import Flask, request, redirect, render_template
import pymysql
import hashlib
import base64
import os  # ← to read environment variables

app = Flask(__name__)

# ✅ Use environment variables for DB connection
def get_db_connection():
    return pymysql.connect(
        host=os.environ.get("MYSQL_HOST"),
        user=os.environ.get("MYSQL_USER"),
        password=os.environ.get("MYSQL_PASSWORD"),
        database=os.environ.get("MYSQL_DB"),
        port=int(os.environ.get("MYSQL_PORT", 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )

# ✅ Function to generate short URL
def generate_short_url(long_url):
    hash_object = hashlib.sha256(long_url.encode())
    short_hash = base64.urlsafe_b64encode(hash_object.digest())[:6].decode()
    return short_hash

# ✅ Home Page
@app.route('/')
def home():
    return render_template('index.html')

# ✅ Shorten the URL
@app.route('/shorten', methods=['POST'])
def shorten_url():
    long_url = request.form.get('long_url')
    if not long_url:
        return "Invalid URL", 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT short_url FROM url_mapping WHERE long_url = %s", (long_url,))
    existing_entry = cursor.fetchone()

    if existing_entry:
        conn.close()
        short = existing_entry['short_url']
        return f"Shortened URL: <a href='/{short}'>{request.host_url}{short}</a>"

    short_url = generate_short_url(long_url)
    cursor.execute(
        "INSERT INTO url_mapping (long_url, short_url, clicks) VALUES (%s, %s, %s)",
        (long_url, short_url, 0)
    )
    conn.commit()
    conn.close()

    return f"Shortened URL: <a href='/{short_url}'>{request.host_url}{short_url}</a>"

# ✅ Redirect from short URL
@app.route('/<short_url>', methods=['GET'])
def redirect_url(short_url):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT long_url FROM url_mapping WHERE short_url = %s", (short_url,))
    entry = cursor.fetchone()

    if entry:
        cursor.execute("UPDATE url_mapping SET clicks = clicks + 1 WHERE short_url = %s", (short_url,))
        conn.commit()
        conn.close()
        return redirect(entry['long_url'])

    conn.close()
    return "Error: URL not found", 404

# ✅ Run app on 0.0.0.0 for Render compatibility
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

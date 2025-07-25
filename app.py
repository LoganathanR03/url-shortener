from flask import Flask, request, redirect, render_template
import pymysql
import hashlib
import base64
import os  # to read environment variables

app = Flask(__name__)

# ✅ Function to connect to MySQL database using environment variables
def get_db_connection():
    return pymysql.connect(
        host=os.environ.get("MYSQL_HOST"),
        user=os.environ.get("MYSQL_USER"),
        password=os.environ.get("MYSQL_PASSWORD"),
        db=os.environ.get("MYSQL_DB"),
        port=int(os.environ.get("MYSQL_PORT")),
        cursorclass=pymysql.cursors.DictCursor
    )

# ✅ Generate a short URL from a hash of the long URL
def generate_short_url(long_url):
    hash_object = hashlib.sha256(long_url.encode())
    short_hash = base64.urlsafe_b64encode(hash_object.digest())[:6].decode()
    return short_hash

# ✅ Render the home page with the form
@app.route('/')
def home():
    return render_template('index.html')

# ✅ Handle POST request to shorten the URL
@app.route('/shorten', methods=['POST'])
def shorten_url():
    long_url = request.form.get('long_url')
    if not long_url:
        return "Invalid URL", 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # 🔄 Check if URL already exists in database
    cursor.execute("SELECT short_url FROM urls WHERE long_url = %s", (long_url,))
    existing_entry = cursor.fetchone()

    if existing_entry:
        conn.close()
        short = existing_entry['short_url']
        return f"Shortened URL: <a href='/{short}'>{request.host_url}{short}</a>"

    # 🔄 Generate a new short URL and insert into DB
    short_url = generate_short_url(long_url)
    cursor.execute(
        "INSERT INTO urls (long_url, short_url) VALUES (%s, %s)",
        (long_url, short_url)
    )
    conn.commit()
    conn.close()

    return f"Shortened URL: <a href='/{short_url}'>{request.host_url}{short_url}</a>"

# ✅ Handle redirect from short URL
@app.route('/<short_url>', methods=['GET'])
def redirect_url(short_url):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT long_url FROM urls WHERE short_url = %s", (short_url,))
    entry = cursor.fetchone()

    if entry:
        conn.close()
        return redirect(entry['long_url'])

    conn.close()
    return "Error: URL not found", 404

# ✅ Run on 0.0.0.0 for deployment compatibility (like Render)
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

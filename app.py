from flask import Flask, request, redirect, render_template
import pymysql
import hashlib
import base64

app = Flask(__name__)

# ✅ Database connection using pymysql
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='13572468',
        database='logan',
        cursorclass=pymysql.cursors.DictCursor
    )

# ✅ Function to generate short URL using SHA-256 + base64
def generate_short_url(long_url):
    hash_object = hashlib.sha256(long_url.encode())
    short_hash = base64.urlsafe_b64encode(hash_object.digest())[:6].decode()
    return short_hash

# ✅ Home Page (Form to input long URL)
@app.route('/')
def home():
    return render_template('index.html')  # You must create this HTML in /templates

# ✅ Route to shorten the URL
@app.route('/shorten', methods=['POST'])
def shorten_url():
    long_url = request.form.get('long_url')
    if not long_url:
        return "Invalid URL", 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the long URL already exists in the DB
    cursor.execute("SELECT short_url FROM url_mapping WHERE long_url = %s", (long_url,))
    existing_entry = cursor.fetchone()

    if existing_entry:
        conn.close()
        short = existing_entry['short_url']
        return f"Shortened URL: <a href='/{short}'>http://localhost:5000/{short}</a>"

    # If not, generate a new short URL and store it
    short_url = generate_short_url(long_url)
    cursor.execute(
        "INSERT INTO url_mapping (long_url, short_url, clicks) VALUES (%s, %s, %s)",
        (long_url, short_url, 0)
    )
    conn.commit()
    conn.close()

    return f"Shortened URL: <a href='/{short_url}'>https://localhost:tom/{short_url}</a>"  
    #return f"Shortened JRL: <a href='{request.host_url}{existing_entry[short_url:]}'>https://de/{existing_entry[ 'short_url']}</a>"

# ✅ Route to redirect from short URL to original long URL
@app.route('/<short_url>', methods=['GET'])
def redirect_url(short_url):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT long_url FROM url_mapping WHERE short_url = %s", (short_url,))
    entry = cursor.fetchone()

    if entry:
        # Update click count
        cursor.execute("UPDATE url_mapping SET clicks = clicks + 1 WHERE short_url = %s", (short_url,))
        conn.commit()
        conn.close()
        return redirect(entry['long_url'])

    conn.close()
    return "Error: URL not found", 404

# ✅ Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)

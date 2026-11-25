"""
Summary: A mini app to serve as an intentionally vulnerable staff portal for
         the mock company Crystal Tokyo. It provides three vulnerable
         endpoints for attack simulation (SQL injection on /search, directory
         traversal on /download, and weak session handling on /login,
         /profile and /logout), and writes one JSON log line per request.
         For local use only.

File: app.py
Authors: Anna Running Rabbit
"""

import hashlib, json, os, sqlite3, threading
from datetime import datetime, timezone

from flask import Flask, Response, g, make_response, redirect, render_template_string, request

# paths can be overridden by environment variables (Docker uses LOG_PATH=/logs/app.log)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", "app.db")
LOG_PATH = os.environ.get("LOG_PATH", "app.log")
FILES_DIR = os.path.join(BASE_DIR, "files")

app = Flask(__name__)
log_lock = threading.Lock()


# Helpers ---------------------------------------------------------------------

def db():
    """Open a new connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)


def utc_now():
    """Current time in UTC, e.g. 2026-11-25T18:02:14Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def client_ip():
    """Client IP address. nginx passes the real client address in X-Real-IP."""
    return request.headers.get("X-Real-IP", request.remote_addr)


def current_sid():
    """Session ID for this request."""
    # VULNERABLE: the session ID is also accepted from the URL (?sid=...)
    return request.args.get("sid") or request.cookies.get("sid")


def current_user():
    """Username for the current session, or None if not logged in."""
    sid = current_sid()
    if not sid:
        return None
    conn = db()
    row = conn.execute("SELECT username FROM sessions WHERE sid = ?", (sid,)).fetchone()
    conn.close()
    return row[0] if row else None


# shared page layout; {{ body|safe }} is safe because each body is rendered
# (and autoescaped) separately in page() before being inserted here
LAYOUT = """<!doctype html>
<title>Crystal Tokyo Staff Portal</title>
<nav>
  <a href="/">Home</a> | <a href="/search">Search</a> | <a href="/download">Files</a> |
  <a href="/profile">Profile</a> |
  {% if user %}Logged in as {{ user }} (<a href="/logout">logout</a>){% else %}<a href="/login">Login</a>{% endif %}
</nav>
<hr>
{{ body|safe }}
"""


def page(body_template, status=200, **context):
    """Render a page body inside the shared layout."""
    body = render_template_string(body_template, **context)
    html = render_template_string(LAYOUT, body=body, user=current_user())
    return html, status


# Logging: one JSON line per request ----------------------------------------

@app.before_request
def reset_request_info():
    """Clear the values that each page fills in for the log."""
    g.sql = None
    g.rows = None
    g.file = None
    g.error = None
    g.user = None


@app.after_request
def log_request(response):
    """Write one JSON line to the app log after every request."""
    entry = {
        "ts": utc_now(),
        "src_ip": client_ip(),
        "method": request.method,
        "path": request.path,
        "query": request.query_string.decode("utf-8", "replace"),
        "status": response.status_code,
        "session_id": current_sid(),
        "user": g.user or current_user(),
        "sql": g.sql,
        "rows_returned": g.rows,
        "file_served": g.file,
        "error": g.error,
    }
    # the lock stops two requests from writing to the file at the same time
    with log_lock:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    return response


# Pages -----------------------------------------------------------------------

@app.route("/")
def index():
    return page("<h1>Crystal Tokyo Staff Portal</h1>"
                "<p>Use Search to look up colleagues and Files to download "
                "documents.</p>")


@app.route("/search")
def search():
    """Staff search. Vulnerable to SQL injection."""
    q = request.args.get("q")
    results, error = [], None

    if q is not None:
        # VULNERABLE: user input is put directly into the SQL text (no ? placeholders)
        g.sql = (f"SELECT full_name, username, email FROM users " 
                 f"WHERE full_name LIKE '%{q}%' OR username LIKE '%{q}%'")
        conn = db()
        try:
            results = conn.execute(g.sql).fetchall()
            g.rows = len(results)
        except sqlite3.Error as e:
            # VULNERABLE: database errors are shown to the user
            error = g.error = str(e)
        conn.close()

    return page("""
        <h2>Staff search</h2>
        <form><input name="q" value="{{ q or '' }}"> <button>Search</button></form>
        {% if error %}<p style="color:red">Database error: {{ error }}</p>{% endif %}
        <ul>{% for r in results %}<li>{{ r[0] }} ({{ r[1] }}) - {{ r[2] }}</li>{% endfor %}</ul>
    """, q=q, results=results, error=error)


@app.route("/download")
def download():
    """Document download. Vulnerable to directory traversal."""
    name = request.args.get("file")

    # no file requested: list the available documents
    if not name:
        files = sorted(os.listdir(FILES_DIR))
        return page("""
            <h2>Documents</h2>
            <ul>{% for f in files %}<li><a href="/download?file={{ f }}">{{ f }}</a></li>{% endfor %}</ul>
        """, files=files)

    # VULNERABLE: no check that the final path stays inside FILES_DIR, so ../ works
    path = os.path.join(FILES_DIR, name)
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        g.error = "file_not_found"
        return page("<p>File not found.</p>", status=404)

    g.file = os.path.normpath(path)
    return Response(data, mimetype="text/plain")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login form. Creates a weak, predictable session."""
    form = """
        <h2>Login</h2>
        {% if failed %}<p style="color:red">Invalid username or password.</p>{% endif %}
        <form method="post">
          <input name="username" placeholder="username">
          <input name="password" type="password" placeholder="password">
          <button>Login</button>
        </form>
    """
    if request.method == "GET":
        return page(form)

    username = request.form.get("username", "")
    password = request.form.get("password", "")
    password_md5 = hashlib.md5(password.encode()).hexdigest()

    # the login query uses ? placeholders, so SQL injection stays limited to /search
    g.sql = "SELECT username FROM users WHERE username = ? AND password_md5 = ?"
    conn = db()
    row = conn.execute(g.sql, (username, password_md5)).fetchone()
    g.rows = 1 if row else 0

    if not row:
        conn.close()
        g.error = "login_failed"
        return page(form, status=401, failed=True)

    # VULNERABLE: session ID is the MD5 of the username - predictable, the same
    # at every login, and never expires
    sid = hashlib.md5(username.encode()).hexdigest()
    conn.execute("INSERT OR IGNORE INTO sessions (sid, username, created_utc) VALUES (?, ?, ?)",
                 (sid, username, utc_now()))
    conn.commit()
    conn.close()

    g.user = username
    response = make_response(redirect("/profile"))
    # VULNERABLE: cookie has no HttpOnly, Secure or SameSite flags
    response.set_cookie("sid", sid)
    return response


@app.route("/profile")
def profile():
    """Shows the logged-in user's details. Target of session hijacking."""
    user = current_user()
    if not user:
        return redirect("/login")

    g.sql = "SELECT username, full_name, email, phone, department FROM users WHERE username = ?"
    conn = db()
    row = conn.execute(g.sql, (user,)).fetchone()
    conn.close()
    g.rows = 1 if row else 0

    return page("""
        <h2>My profile</h2>
        <table>
          <tr><td>Username</td><td>{{ r[0] }}</td></tr>
          <tr><td>Name</td><td>{{ r[1] }}</td></tr>
          <tr><td>Email</td><td>{{ r[2] }}</td></tr>
          <tr><td>Phone</td><td>{{ r[3] }}</td></tr>
          <tr><td>Department</td><td>{{ r[4] }}</td></tr>
        </table>
    """, r=row)


@app.route("/logout")
def logout():
    # VULNERABLE: only the cookie is cleared; the session stays valid in the database
    response = make_response(redirect("/"))
    response.delete_cookie("sid")
    return response


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
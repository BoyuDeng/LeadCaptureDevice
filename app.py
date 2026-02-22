from __future__ import annotations

import html
import sqlite3
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "leads.db"


def init_db(db_path: Path | None = None) -> None:
    db_path = db_path or DB_PATH
    db = sqlite3.connect(db_path)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            company TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()
    db.close()


def insert_lead(name: str, email: str, company: str, message: str, db_path: Path | None = None) -> None:
    db_path = db_path or DB_PATH
    db = sqlite3.connect(db_path)
    db.execute(
        "INSERT INTO leads (name, email, company, message) VALUES (?, ?, ?, ?)",
        (name, email, company, message),
    )
    db.commit()
    db.close()


def get_leads(db_path: Path | None = None):
    db_path = db_path or DB_PATH
    db = sqlite3.connect(db_path)
    rows = db.execute(
        "SELECT name, email, company, message, created_at FROM leads ORDER BY created_at DESC"
    ).fetchall()
    db.close()
    return rows


def render_page(message: str = "", is_error: bool = False) -> str:
    leads = get_leads()
    rows = "".join(
        f"<tr><td>{html.escape(name)}</td><td>{html.escape(email)}</td>"
        f"<td>{html.escape(company or '-')}</td><td>{html.escape(notes or '-')}</td><td>{html.escape(created)}</td></tr>"
        for name, email, company, notes, created in leads
    )
    alert = ""
    if message:
        klass = "error" if is_error else "success"
        alert = f'<div class="flash {klass}">{html.escape(message)}</div>'

    return f"""<!doctype html>
<html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Lead Capture Device</title>
<link rel='stylesheet' href='/styles.css'>
</head><body>
<main class='container'>
  <h1>Lead Capture Device</h1>
  <p class='subtitle'>Collect and manage inbound leads in one place.</p>
  {alert}
  <section class='card'>
    <h2>Add New Lead</h2>
    <form method='post'>
      <label>Name*<input name='name' required></label>
      <label>Email*<input name='email' type='email' required></label>
      <label>Company<input name='company'></label>
      <label>Notes<textarea name='message' rows='4'></textarea></label>
      <button type='submit'>Save Lead</button>
    </form>
  </section>
  <section class='card'>
    <h2>Recent Leads</h2>
    <table><thead><tr><th>Name</th><th>Email</th><th>Company</th><th>Notes</th><th>Created</th></tr></thead>
    <tbody>{rows}</tbody></table>
  </section>
</main></body></html>"""


STYLES = """
body { font-family: Arial, sans-serif; margin: 0; background: #f5f7fb; color: #1b2a3a; }
.container { max-width: 920px; margin: 2rem auto; padding: 1rem; }
.subtitle { color: #5b6f82; }
.card { background: white; border-radius: 12px; padding: 1rem; margin-top: 1rem; box-shadow: 0 4px 14px rgba(0,0,0,0.08); }
form { display: grid; gap: .8rem; grid-template-columns: 1fr 1fr; }
label { display: flex; flex-direction: column; gap: .4rem; }
textarea, button { grid-column: 1/-1; }
input, textarea { border: 1px solid #cfd8e3; border-radius: 8px; padding: .55rem; }
button { border: 0; border-radius: 8px; background: #0f62fe; color: #fff; padding: .7rem 1rem; cursor: pointer; }
table { width: 100%; border-collapse: collapse; }
th,td { text-align: left; border-bottom: 1px solid #e8edf4; padding: .55rem; }
.flash { border-radius: 8px; padding: .6rem .8rem; margin: .8rem 0; }
.success { background: #dafbe1; }
.error { background: #ffebe9; }
"""


def application(environ, start_response):
    method = environ["REQUEST_METHOD"]
    path = environ.get("PATH_INFO", "/")

    if path == "/styles.css":
        start_response("200 OK", [("Content-Type", "text/css; charset=utf-8")])
        return [STYLES.encode("utf-8")]

    if path == "/" and method == "GET":
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [render_page().encode("utf-8")]

    if path == "/" and method == "POST":
        length = int(environ.get("CONTENT_LENGTH") or 0)
        body = environ["wsgi.input"].read(length).decode("utf-8")
        form = parse_qs(body)

        name = form.get("name", [""])[0].strip()
        email = form.get("email", [""])[0].strip()
        company = form.get("company", [""])[0].strip()
        message = form.get("message", [""])[0].strip()

        if not name or not email:
            start_response("400 Bad Request", [("Content-Type", "text/html; charset=utf-8")])
            return [render_page("Name and email are required.", is_error=True).encode("utf-8")]

        insert_lead(name, email, company, message)
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [render_page("Lead captured successfully!").encode("utf-8")]

    start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
    return [b"Not found"]


if __name__ == "__main__":
    init_db()
    with make_server("0.0.0.0", 5000, application) as httpd:
        print("Serving on http://0.0.0.0:5000")
        httpd.serve_forever()

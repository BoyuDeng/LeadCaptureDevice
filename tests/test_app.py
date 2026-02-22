import io
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app


def setup_temp_db(tmp_path: Path):
    db_path = tmp_path / "test.db"
    app.DB_PATH = db_path
    app.init_db(db_path)
    return db_path


def call_app(method="GET", path="/", body=""):
    body_bytes = body.encode("utf-8")
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_LENGTH": str(len(body_bytes)),
        "wsgi.input": io.BytesIO(body_bytes),
    }
    status_holder = {}

    def start_response(status, headers):
        status_holder["status"] = status
        status_holder["headers"] = headers

    response = b"".join(app.application(environ, start_response)).decode("utf-8")
    return status_holder["status"], dict(status_holder["headers"]), response


def test_homepage_loads(tmp_path):
    setup_temp_db(tmp_path)
    status, _, body = call_app("GET", "/")
    assert status.startswith("200")
    assert "Lead Capture Device" in body


def test_create_lead(tmp_path):
    db_path = setup_temp_db(tmp_path)
    payload = "name=Ada&email=ada%40example.com&company=Analytical&message=High+intent"
    status, _, body = call_app("POST", "/", payload)
    assert status.startswith("200")
    assert "Lead captured successfully" in body

    db = sqlite3.connect(db_path)
    row = db.execute("SELECT name, email FROM leads LIMIT 1").fetchone()
    db.close()
    assert row == ("Ada", "ada@example.com")


def test_validation_requires_name_and_email(tmp_path):
    setup_temp_db(tmp_path)
    status, _, body = call_app("POST", "/", "name=&email=")
    assert status.startswith("400")
    assert "Name and email are required." in body

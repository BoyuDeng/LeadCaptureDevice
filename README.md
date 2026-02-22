# Lead Capture Device

A lightweight lead capture web app built with Python's standard library and SQLite.

## Requirements
- Python 3.10+
- `pytest` (only needed if you want to run tests)

## How to run
From the repository root:

```bash
python app.py
```

You should see:

```text
Serving on http://0.0.0.0:5000
```

Then open:
- `http://localhost:5000` (same machine)
- or `http://127.0.0.1:5000`

The SQLite database file (`leads.db`) is created automatically on first run.

## How to use
1. Fill in **Name** and **Email** (required).
2. Optionally add **Company** and **Notes**.
3. Click **Save Lead**.
4. Your saved lead appears in the **Recent Leads** table.

## Run tests
```bash
pytest -q
```

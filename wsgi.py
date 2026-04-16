"""
WSGI entry point for production servers (Render, PythonAnywhere, gunicorn).

Gunicorn start command:
    gunicorn wsgi:app

This file lives at the project root, so the root is on sys.path and
'from app import ...' resolves correctly to the app/ package.
"""
import os
import sys

# Guarantee the project root is on the path regardless of how the process
# is started (handles edge cases with some WSGI servers).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

app = create_app()

# Create all database tables on startup (safe to call repeatedly —
# SQLAlchemy skips tables that already exist).
with app.app_context():
    db.create_all()

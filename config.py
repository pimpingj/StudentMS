import os


class Config:
    # ── Secret key ────────────────────────────────────────────────────────────
    # Set the SECRET_KEY environment variable in production.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'csy4022-studentms-secret-changeme')

    # ── Database ──────────────────────────────────────────────────────────────
    # Connection string is built from individual DB_* environment variables so
    # each value can be set separately in Render (or any host) without exposing
    # credentials in source code.
    #
    # Required env vars for production:
    #   DB_HOST     e.g. sql8.freesqldatabase.com
    #   DB_PORT     e.g. 3306
    #   DB_NAME     e.g. sql8823462
    #   DB_USER     e.g. sql8823462
    #   DB_PASS     your database password
    #
    # Falls back to local MySQL with no password when env vars are absent.
    _db_host = os.environ.get('DB_HOST', 'localhost')
    _db_port = os.environ.get('DB_PORT', '3306')
    _db_name = os.environ.get('DB_NAME', 'sms_db')
    _db_user = os.environ.get('DB_USER', 'root')
    _db_pass = os.environ.get('DB_PASS', '')

    # DATABASE_URL overrides all individual vars if set (e.g. PythonAnywhere).
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'mysql+pymysql://{_db_user}:{_db_pass}@{_db_host}:{_db_port}/{_db_name}'
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Always False in production. Enable locally by setting FLASK_DEBUG=1.
    DEBUG = False
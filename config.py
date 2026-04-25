import os


class Config:
    # ── Secret key ────────────────────────────────────────────────────────────
    # Set the SECRET_KEY environment variable in production.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'csy4022-studentms-secret-changeme')

    # ── Database ──────────────────────────────────────────────────────────────
    # TODO: move credentials to environment variables once deployment is stable.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///studentms.db'
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Always False in production. Enable locally by setting FLASK_DEBUG=1.
    DEBUG = False
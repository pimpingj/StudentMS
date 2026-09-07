import os
import secrets

def _load_secret_key():
    key = os.environ.get('SECRET_KEY')
    if key:
        return key
    if os.environ.get('FLASK_DEBUG') == '1':
        return secrets.token_hex(32)
    raise RuntimeError(
        'SECRET_KEY is not set. '
        'Set the SECRET_KEY environment variable before starting the app.'
    )


class Config:
    SECRET_KEY = _load_secret_key()

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///studentms.db'
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False

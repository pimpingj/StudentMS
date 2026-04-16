import os


class Config:
    # Set SECRET_KEY in your environment for production.
    # Example (Linux/Mac): export SECRET_KEY='some-long-random-string'
    # PythonAnywhere: add to the WSGI file as os.environ['SECRET_KEY'] = '...'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'csy4022-studentms-secret-changeme')

    # Local default connects to a root MySQL with no password.
    # Override via DATABASE_URL environment variable for any other environment.
    # PythonAnywhere format:
    #   mysql+pymysql://<username>:<password>@<username>.mysql.pythonanywhere-services.com/<username>$sms_db
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'mysql+pymysql://root:@localhost:3306/sms_db'
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Always False in production. Enable locally by setting FLASK_DEBUG=1.
    DEBUG = False
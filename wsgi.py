import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

app = create_app()

with app.app_context():
    db.create_all()
    from app.models import User
    if User.query.count() == 0:
        print("Empty database detected — seeding...")
        from init_remote_db import seed
        seed()

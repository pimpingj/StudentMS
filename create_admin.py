from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():

    existing = User.query.filter_by(username='admin').first()
    if existing:
        db.session.delete(existing)
        db.session.commit()


    admin = User(username='admin', role='admin')
    admin.set_password('123456')
    db.session.add(admin)
    db.session.commit()
    print('Admin created successfully.')

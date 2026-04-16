import os
from app import create_app, db
from sqlalchemy import inspect

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)
        print(inspector.get_table_names())
    # Enable debug mode locally by setting the environment variable:
    #   Windows:   set FLASK_DEBUG=1
    #   Mac/Linux: export FLASK_DEBUG=1
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug)
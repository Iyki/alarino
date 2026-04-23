from alarino_backend import create_app
from alarino_backend.db_models import db


def create_tables(app=None):
    app = app or create_app()
    with app.app_context():
        print("trying")
        # db.drop_all()
        # db.create_all()  # this creates all tables based on the models
        print("Tables created successfully.")


if __name__ == '__main__':
    create_tables()

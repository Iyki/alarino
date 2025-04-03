from alarino_backend import app
from alarino_backend.shared_utils.db_models import db

def create_tables():
    with app.app_context():
        print("trying")
        # db.drop_all()
        db.create_all()  # this creates all tables based on the models
        print("Tables created successfully.")

if __name__ == '__main__':
    create_tables()
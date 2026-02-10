from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()

def delete_all_users():
    with app.app_context():
        try:
            num_deleted = db.session.query(User).delete()
            db.session.commit()
            print(f"Successfully deleted {num_deleted} users.")
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting users: {e}")

if __name__ == "__main__":
    delete_all_users()

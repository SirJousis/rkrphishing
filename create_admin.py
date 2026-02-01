from app import create_app
from app.extensions import db
from app.models.client import Client
from app.models.user import User
from werkzeug.security import generate_password_hash

app = create_app()

def create_admin_user():
    with app.app_context():
        # Ensure Admin Client exists
        admin_client = Client.query.filter_by(name="Admin Org").first()
        if not admin_client:
            print("Creating Admin Org client...")
            admin_client = Client(name="Admin Org")
            db.session.add(admin_client)
            db.session.commit()
        
        username = input("Enter Admin Username: ")
        password = input("Enter Admin Password: ")
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            print(f"User {username} already exists.")
            return

        print(f"Creating admin user {username}...")
        admin_user = User(
            client_id=admin_client.id,
            username=username,
            password_hash=generate_password_hash(password),
            role="admin"
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created successfully!")

if __name__ == "__main__":
    create_admin_user()

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.client import Client
from app.models.campaign import Campaign
from app.models.event import Event
from app.models.session import VisitSession
from app.models.landing import Landing

app = create_app()

def cleanup_database():
    with app.app_context():
        print("Starting database cleanup...")

        # 1. Identify admin user and their client
        admin_user = User.query.filter_by(username="admin").first()
        if not admin_user:
            print("Error: 'admin' user not found. Cleanup aborted to prevent complete lock-out.")
            return

        admin_client_id = admin_user.client_id
        print(f"Keeping Admin User (ID: {admin_user.id}) and Client (ID: {admin_client_id})")

        # 2. Delete all events and sessions (safe to clear all)
        print("Deleting all events and sessions...")
        Event.query.delete()
        VisitSession.query.delete()

        # 3. Delete all landings and campaigns
        print("Deleting all landings and campaigns...")
        Landing.query.delete()
        Campaign.query.delete()

        # 4. Delete users except 'admin'
        print("Deleting users (except admin)...")
        User.query.filter(User.username != "admin").delete()

        # 5. Delete clients except the admin's client
        print("Deleting clients (except admin organization)...")
        Client.query.filter(Client.id != admin_client_id).delete()

        db.session.commit()
        print("\nCleanup complete!")
        print(f"Remaining Users: {[u.username for u in User.query.all()]}")
        print(f"Remaining Clients: {[c.name for c in Client.query.all()]}")

if __name__ == "__main__":
    cleanup_database()

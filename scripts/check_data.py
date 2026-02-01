from app import create_app
from app.extensions import db
from app.models.client import Client
from app.models.user import User
from app.models.campaign import Campaign
from app.models.event import Event
from app.models.session import VisitSession

app = create_app()

def check_data():
    with app.app_context():
        print("--- Data Check ---")
        print(f"Clients: {Client.query.count()}")
        for c in Client.query.all():
            print(f" - Client: {c.name} (ID: {c.id}) API Key: {c.api_key}")
            
        print(f"Users: {User.query.count()}")
        for u in User.query.all():
            print(f" - User: {u.username} (Role: {u.role}) Client ID: {u.client_id}")

        print(f"Campaigns: {Campaign.query.count()}")
        for c in Campaign.query.all():
            print(f" - Campaign: {c.name} (ID: {c.id}) Client ID: {c.client_id}")

        print(f"Sessions: {VisitSession.query.count()}")
        print(f"Events: {Event.query.count()}")
        for e in Event.query.all():
             print(f" - Event: {e.event_type} Client ID: {e.client_id}")

if __name__ == "__main__":
    check_data()

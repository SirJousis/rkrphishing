from app import create_app
from app.extensions import db
from app.models.client import Client
from app.models.campaign import Campaign

app = create_app()

def create_admin_campaign():
    with app.app_context():
        # Get Admin Org (Client ID 1)
        client = Client.query.get(1)
        if not client:
            print("Error: Client ID 1 not found.")
            return

        # Create new campaign
        campaign = Campaign(client_id=client.id, name="Campaña Principal")
        db.session.add(campaign)
        db.session.commit()
        
        print(f"Nueva Campaña Creada: {campaign.name}")
        print(f"Campaign ID: {campaign.id}")
        print(f"API Key: {client.api_key}")

if __name__ == "__main__":
    create_admin_campaign()

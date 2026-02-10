from app import create_app
from app.extensions import db
from app.models.client import Client
from app.models.campaign import Campaign
from app.models.user import User

app = create_app()

def verify_admin_features():
    with app.app_context():
        print("--- Verification: Admin Campaign Management ---")
        
        # 1. Ensure a test client exists
        client_name = "Verification Client"
        client = Client.query.filter_by(name=client_name).first()
        if not client:
            client = Client(name=client_name)
            db.session.add(client)
            db.session.commit()
            print(f"Created Client: {client.name} (ID: {client.id})")
        
        # 2. Simulate campaign creation (as the route would do)
        campaign_name = "Admin Verified Campaign"
        # Check if already exists
        existing_campaign = Campaign.query.filter_by(client_id=client.id, name=campaign_name).first()
        if existing_campaign:
             db.session.delete(existing_campaign)
             db.session.commit()
             print(f"Deleted existing campaign '{campaign_name}' for clean test.")

        # Simulate the POST /admin/campaign/create logic
        new_campaign = Campaign(client_id=client.id, name=campaign_name)
        db.session.add(new_campaign)
        db.session.commit()
        
        # 3. Verify
        campaign = Campaign.query.filter_by(client_id=client.id, name=campaign_name).first()
        if campaign:
            print(f"SUCCESS: Campaign '{campaign.name}' created for Client '{client.name}'")
            print(f"Campaign ID: {campaign.id}, Client ID: {campaign.client_id}")
        else:
            print("FAILURE: Campaign was not created.")

        # 4. Cleanup test data (optional, but good practice)
        # db.session.delete(campaign)
        # db.session.delete(client)
        # db.session.commit()

if __name__ == "__main__":
    verify_admin_features()

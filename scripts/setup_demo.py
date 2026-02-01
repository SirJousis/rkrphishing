from app import create_app
from app.extensions import db
from app.models.client import Client
from app.models.user import User
from app.models.campaign import Campaign
from app.models.landing import Landing

app = create_app()

def setup_test_campaign():
    with app.app_context():
        # 1. Identify current user/client (Based on previous check_data.py)
        # User: Jose (ID: 2) belongs to Client: Test (ID: 2)
        client = Client.query.get(2)
        if not client:
            print("Error: Client ID 2 not found. Run check_data.py to verify IDs.")
            return

        print(f"Setting up campaign for Client: {client.name} (ID: {client.id})")
        print(f"API KEY: {client.api_key}")

        # 2. Create a specific campaign if it doesn't exist
        campaign_name = "Demo Phishing Feb"
        campaign = Campaign.query.filter_by(client_id=client.id, name=campaign_name).first()
        
        if not campaign:
            campaign = Campaign(client_id=client.id, name=campaign_name)
            db.session.add(campaign)
            db.session.commit()
            print(f"Created Campaign: {campaign.name} (ID: {campaign.id})")
        else:
            print(f"Using Existing Campaign: {campaign.name} (ID: {campaign.id})")

        # 3. Create a landing page entry
        landing = Landing.query.filter_by(campaign_id=campaign.id).first()
        if not landing:
            landing = Landing(
                client_id=client.id,
                campaign_id=campaign.id,
                name="Microsoft Login Clone",
                url="http://127.0.0.1:8080/login.html" # Mock URL
            )
            db.session.add(landing)
            db.session.commit()
            print(f"Created Landing Page entry (ID: {landing.id})")
        
        print("\n--- END-TO-END TEST INFO ---")
        print(f"1. Use this API Key in your script: {client.api_key}")
        print(f"2. Use this Campaign ID in your script: {campaign.id}")
        print("----------------------------")

if __name__ == "__main__":
    setup_test_campaign()

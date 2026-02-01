from app import create_app
from app.extensions import db
from app.models.client import Client
from app.models.campaign import Campaign
from datetime import datetime, timedelta

app = create_app()

def create_test_campaign():
    with app.app_context():
        clients = Client.query.all()
        for client in clients:
            # Check for existing campaign
            camp = Campaign.query.filter_by(name="Default Campaign", client_id=client.id).first()
            if camp:
                 print(f"Campaign already exists for {client.name}. ID: {camp.id}")
                 continue

            print(f"Creating Default Campaign for {client.name}...")
            camp = Campaign(
                client_id=client.id,
                name="Default Campaign",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(camp)
        
        db.session.commit()
        print("Campaigns created successfully!")

if __name__ == "__main__":
    create_test_campaign()

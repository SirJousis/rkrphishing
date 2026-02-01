from app import create_app
from app.extensions import db
from app.models.client import Client
from app.models.campaign import Campaign
from app.models.event import Event
from app.models.session import VisitSession
import uuid

# Setup
app = create_app()

def run_test():
    with app.app_context():
        # 1. Ensure a test client exists
        client = Client.query.filter_by(name="Test Client").first()
        if not client:
            client = Client(name="Test Client")
            db.session.add(client)
            db.session.commit()
            print(f"Created Test Client with API Key: {client.api_key}")
        else:
            print(f"Using Test Client with API Key: {client.api_key}")
            
        # 2. Ensure a test campaign exists
        campaign = Campaign.query.filter_by(name="Test Campaign").first()
        if not campaign:
            campaign = Campaign(client_id=client.id, name="Test Campaign")
            db.session.add(campaign)
            db.session.commit()
            print(f"Created Test Campaign ID: {campaign.id}")
        else:
            print(f"Using Test Campaign ID: {campaign.id}")

        # 3. Simulate a POST request to /track (using requests usually requires the server running, 
        # but here we can check if we can simulate it with test_client)
        
        test_client = app.test_client()
        
        payload = {
            "api_key": client.api_key,
            "campaign_id": campaign.id,
            "event_type": "visit",
            "session_uuid": None, # Should generate new
            "event_data": {"url": "http://test.com", "referrer": "http://google.com"}
        }
        
        print("\nSending POST /track request...")
        response = test_client.post('/track', json=payload)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.get_json()}")
        
        if response.status_code == 200:
            # 4. Verify DB
            events_count = Event.query.filter_by(client_id=client.id).count()
            sessions_count = VisitSession.query.filter_by(client_id=client.id).count()
            print(f"\nDB Verification:")
            print(f"Events Found: {events_count}")
            print(f"Sessions Found: {sessions_count}")
            
            if events_count > 0 and sessions_count > 0:
                print("SUCCESS: Tracking works from backend perspective.")
            else:
                print("FAILURE: Response 200 but data not in DB??")
        else:
            print("FAILURE: Request failed.")

if __name__ == "__main__":
    run_test()

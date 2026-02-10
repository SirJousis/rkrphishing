from app.main import create_app
from app.extensions import db
from app.models.monitored_domain import MonitoredDomain
from app.models.discovered_domain import DiscoveredDomain

app = create_app()

def update_db():
    with app.app_context():
        print("Ensuring new tables exist...")
        db.create_all()
        print("Database updated successfully.")

if __name__ == "__main__":
    update_db()

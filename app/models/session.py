from app.extensions import db
from datetime import datetime

class VisitSession(db.Model):
    __tablename__ = "visit_sessions"
    __table_args__ = {"mysql_engine": "InnoDB"}


    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"))
    landing_id = db.Column(db.Integer, db.ForeignKey("landings.id"))

    session_uuid = db.Column(db.String(64), unique=True, index=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)

    started_at = db.Column(db.DateTime, default=datetime.utcnow)

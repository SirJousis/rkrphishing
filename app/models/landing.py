from app.extensions import db
from datetime import datetime

class Landing(db.Model):
    __tablename__ = "landings"
    __table_args__ = {"mysql_engine": "InnoDB"}


    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=False)

    name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(512), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    campaign = db.relationship("Campaign", backref="landings")
    client = db.relationship("Client", backref="landings")

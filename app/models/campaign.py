from app.extensions import db
from datetime import datetime

class Campaign(db.Model):
    __tablename__ = "campaigns"
    __table_args__ = {"mysql_engine": "InnoDB"}


    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)

    name = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    client = db.relationship("Client", backref="campaigns")

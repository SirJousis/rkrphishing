from app.extensions import db
from datetime import datetime

class MonitoredDomain(db.Model):
    __tablename__ = "monitored_domains"
    __table_args__ = {"mysql_engine": "InnoDB"}

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    domain = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    client = db.relationship("Client", backref=db.backref("monitored_domains", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<MonitoredDomain {self.domain}>"

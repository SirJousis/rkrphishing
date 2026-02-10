from app.extensions import db
from datetime import datetime

class DiscoveredDomain(db.Model):
    __tablename__ = "discovered_domains"
    __table_args__ = {"mysql_engine": "InnoDB"}

    id = db.Column(db.Integer, primary_key=True)
    monitored_domain_id = db.Column(db.Integer, db.ForeignKey("monitored_domains.id"), nullable=False)
    domain = db.Column(db.String(255), nullable=False)
    status = db.Column(
        db.Enum("potential", "malicious", "whitelisted", name="discovery_status"),
        default="potential",
        nullable=False
    )
    discovered_at = db.Column(db.DateTime, default=datetime.utcnow)

    monitored_domain = db.relationship("MonitoredDomain", backref=db.backref("discovered_domains", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<DiscoveredDomain {self.domain} ({self.status})>"

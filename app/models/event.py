from app.extensions import db
from datetime import datetime

class Event(db.Model):
    __tablename__ = "events"
    __table_args__ = {"mysql_engine": "InnoDB"}


    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey("visit_sessions.id"), nullable=False)

    event_type = db.Column(
        db.Enum(
            "visit",
            "click",
            "credentials_submitted",
            "time_on_page",
            name="event_types"
        ),
        nullable=False
    )

    event_data = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    session = db.relationship("VisitSession", backref="events")

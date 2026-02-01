from app.extensions import db
from datetime import datetime
import secrets

class Client(db.Model):
    __tablename__ = "clients"
    __table_args__ = {"mysql_engine": "InnoDB"}


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)

    api_key = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
        default=lambda: secrets.token_hex(32)
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

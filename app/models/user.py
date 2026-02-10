from app.extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = {"mysql_engine": "InnoDB"}

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)

    username = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(
        db.Enum("admin", "analyst", name="user_roles"),
        default="analyst",
        nullable=False
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    client = db.relationship("Client", backref="users")
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

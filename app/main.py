from flask import Flask
from app.config.settings import Config
from app.routes.track import track_bp
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.monitoring import monitoring_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(track_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(monitoring_bp)

    return app

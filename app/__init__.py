from flask import Flask
from app.extensions import db, login_manager
from flask_cors import CORS
from app.routes.api_keys import api_keys_bp
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    CORS(app) # Enable CORS for all routes (for now)

    # DEBUG
    print("INSTANCE PATH:", app.instance_path)

    # Cargar config
    app.config.from_pyfile("config.py", silent=False)

    print("DB URI LOADED:", app.config.get("SQLALCHEMY_DATABASE_URI"))

    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("SQLALCHEMY_DATABASE_URI NOT LOADED")
    
    # endpoints
    app.register_blueprint(api_keys_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp)
    
    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)


    db.init_app(app)
    login_manager.init_app(app)  
    from app.routes.track import track_bp
    app.register_blueprint(track_bp)

    return app

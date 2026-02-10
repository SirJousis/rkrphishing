import os
from flask import Flask
from app.extensions import db, login_manager
from flask_cors import CORS
from app.routes.api_keys import api_keys_bp
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.monitoring import monitoring_bp

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    CORS(app) # Enable CORS for all routes (for now)

    # DEBUG
    print("INSTANCE PATH:", app.instance_path)

    # Cargar config
    # Primero intentamos cargar desde instance/config.py si existe
    app.config.from_pyfile("config.py", silent=True)
    
    # Luego sobrescribimos con variables de entorno si están presentes
    if os.getenv("DATABASE_URL"):
        app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    if os.getenv("SECRET_KEY"):
        app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    print("DB URI LOADED:", app.config.get("SQLALCHEMY_DATABASE_URI"))

    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("SQLALCHEMY_DATABASE_URI NOT LOADED. Please set DATABASE_URL environment variable or configure instance/config.py")
    
    # endpoints
    app.register_blueprint(api_keys_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(monitoring_bp)
    
    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)


    db.init_app(app)
    login_manager.init_app(app)  
    from app.routes.track import track_bp
    app.register_blueprint(track_bp)

    # Root routes and favicon
    from flask import redirect, url_for
    from flask_login import current_user

    @app.route("/")
    @app.route("/index.html")
    def index_redirect():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.index"))
        return redirect(url_for("auth.login"))

    @app.route("/favicon.ico")
    def favicon():
        return "", 204

    return app

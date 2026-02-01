from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models.client import Client
from app.models.user import User
from app.models.campaign import Campaign

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Middleware para asegurar que solo admin accede
@admin_bp.before_request
@login_required
def require_admin():
    if current_user.role != "admin":
        return "Forbidden", 403

@admin_bp.route("/")
def index():
    clients = Client.query.all()
    campaigns = Campaign.query.all()
    users = User.query.all()
    return render_template("admin/index.html", clients=clients, campaigns=campaigns, users=users)

@admin_bp.route("/client/create", methods=["POST"])
def create_client():
    name = request.form.get("name")
    if not name:
        flash("Client name is required")
        return redirect(url_for("admin.index"))
    
    if Client.query.filter_by(name=name).first():
        flash("Client already exists")
        return redirect(url_for("admin.index"))

    new_client = Client(name=name)
    db.session.add(new_client)
    db.session.commit()
    
    flash(f"Client {name} created successfully")
    return redirect(url_for("admin.index"))

@admin_bp.route("/client/update/<int:id>", methods=["POST"])
def update_client(id):
    client = Client.query.get_or_404(id)
    name = request.form.get("name")
    if name:
        client.name = name
        db.session.commit()
        flash(f"Client {id} updated successfully")
    return redirect(url_for("admin.index"))

@admin_bp.route("/client/delete/<int:id>", methods=["POST"])
def delete_client(id):
    if id == 1: # Prevent deleting Admin Org
        flash("Cannot delete Admin Organization")
        return redirect(url_for("admin.index"))
    
    client = Client.query.get_or_404(id)
    
    try:
        # Import models needed for deletion
        from app.models.event import Event
        from app.models.session import VisitSession
        from app.models.landing import Landing
        from app.models.campaign import Campaign
        
        # Delete in correct order to respect foreign key constraints
        # 1. Delete events (depends on sessions and client)
        Event.query.filter_by(client_id=id).delete()
        
        # 2. Delete sessions (depends on client, campaign, landing)
        VisitSession.query.filter_by(client_id=id).delete()
        
        # 3. Delete landings (depends on client and campaign)
        Landing.query.filter_by(client_id=id).delete()
        
        # 4. Delete campaigns (depends on client)
        Campaign.query.filter_by(client_id=id).delete()
        
        # 5. Delete users (depends on client)
        User.query.filter_by(client_id=id).delete()
        
        # 6. Finally delete the client
        db.session.delete(client)
        db.session.commit()
        
        flash(f"Client {client.name} and all related data deleted successfully")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting client: {str(e)}")
    
    return redirect(url_for("admin.index"))

@admin_bp.route("/user/create", methods=["POST"])
def create_user():
    client_id = request.form.get("client_id")
    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role", "analyst")

    if not all([client_id, username, password]):
        flash("All fields are required")
        return redirect(url_for("admin.index"))

    if User.query.filter_by(username=username).first():
        flash("Username already registered")
        return redirect(url_for("admin.index"))

    hashed_pw = generate_password_hash(password)
    new_user = User(
        client_id=client_id, 
        username=username, 
        password_hash=hashed_pw,
        role=role
    )
    db.session.add(new_user)
    db.session.commit()

    flash(f"User {username} created for client ID {client_id}")
    return redirect(url_for("admin.index"))

@admin_bp.route("/campaign/create", methods=["POST"])
def create_campaign():
    client_id = request.form.get("client_id")
    name = request.form.get("name")

    if not all([client_id, name]):
        flash("All fields are required")
        return redirect(url_for("admin.index"))

    # Verify client exists
    client = Client.query.get(client_id)
    if not client:
        flash("Invalid client selected")
        return redirect(url_for("admin.index"))

    new_campaign = Campaign(client_id=client_id, name=name)
    db.session.add(new_campaign)
    db.session.commit()

    flash(f"Campaign '{name}' created for client {client.name}")
    return redirect(url_for("admin.index"))

@admin_bp.route("/user/update/<int:id>", methods=["POST"])
def update_user(id):
    user = User.query.get_or_404(id)
    username = request.form.get("username")
    password = request.form.get("password")
    client_id = request.form.get("client_id")
    role = request.form.get("role")

    if username:
        user.username = username
    if password:
        user.password_hash = generate_password_hash(password)
    if client_id:
        user.client_id = client_id
    if role:
        user.role = role
        
    db.session.commit()
    flash(f"User {user.username} updated")
    return redirect(url_for("admin.index"))

@admin_bp.route("/user/delete/<int:id>", methods=["POST"])
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.username == "admin":
        flash("Cannot delete admin user")
        return redirect(url_for("admin.index"))
        
    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.username} deleted")
    return redirect(url_for("admin.index"))

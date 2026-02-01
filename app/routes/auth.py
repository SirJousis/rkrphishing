from flask import Blueprint, request, jsonify, redirect, url_for, render_template
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from app.models.user import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON"}), 400

    user = User.query.filter_by(username=data.get("username")).first()

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if not check_password_hash(user.password_hash, data.get("password")):
        return jsonify({"error": "Invalid credentials"}), 401

    login_user(user)
    return jsonify({"status": "ok"})

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login")) # Or wherever

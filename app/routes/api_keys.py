from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
import secrets

api_keys_bp = Blueprint("api_keys", __name__)

@api_keys_bp.route("/dashboard/api-key")
@login_required
def view_api_key():
    client = current_user.client
    return render_template(
        "dashboard/api_key.html",
        client=client,
        api_key=client.api_key,
        is_admin=current_user.role == "admin"
    )


@api_keys_bp.route("/dashboard/api-key/rotate", methods=["POST"])
@login_required
def rotate_api_key():
    if current_user.role != "admin":
        return "Forbidden", 403

    current_user.client.api_key = secrets.token_hex(32)
    db.session.commit()
    return redirect(url_for("api_keys.view_api_key"))

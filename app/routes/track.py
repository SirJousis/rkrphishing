from flask import Blueprint, request, jsonify
from app.extensions import db
from app.auth.api_key import require_api_key
from app.models.session import VisitSession
from app.models.event import Event
import uuid

track_bp = Blueprint("track", __name__)

def sanitize_event_data(event_data):
    """
    Remove sensitive information from event data before storing.
    This prevents passwords and other sensitive data from being stored in the database.
    """
    if not event_data or not isinstance(event_data, dict):
        return event_data
    
    # List of sensitive field names to remove (case-insensitive)
    sensitive_fields = [
        'password', 'passwd', 'pwd', 'pass',
        'password1', 'password2', 'confirm_password',
        'secret', 'token', 'api_key', 'apikey',
        'credit_card', 'creditcard', 'cvv', 'ssn',
        'pin', 'security_answer'
    ]
    
    # Create a copy to avoid modifying the original
    sanitized = event_data.copy()
    
    # Remove sensitive fields
    for key in list(sanitized.keys()):
        if key.lower() in sensitive_fields:
            # Replace with a marker instead of storing the actual value
            sanitized[key] = "[REDACTED]"
    
    return sanitized

@track_bp.route("/track", methods=["POST"])
@require_api_key
def track():
    data = request.get_json(force=True, silent=True) or {}

    # Cliente resuelto por API key
    client = request.client

    session_uuid = data.get("session_uuid") or uuid.uuid4().hex
    event_type = data.get("event_type")

    if not event_type:
        return jsonify({"error": "event_type required"}), 400

    # Obtener o crear sesión
    session = VisitSession.query.filter_by(
        session_uuid=session_uuid
    ).first()

    campaign_id = data.get("campaign_id")
    if campaign_id:
        from app.models.campaign import Campaign
        campaign = Campaign.query.filter_by(id=campaign_id, client_id=client.id).first()
        if not campaign:
            return jsonify({"error": "Invalid campaign_id for this client"}), 400

    if not session:
        print(f"[TRACK] Creating new session for client {client.id}, campaign {campaign_id}")
        session = VisitSession(
            client_id=client.id,
            campaign_id=campaign_id,
            landing_id=data.get("landing_id"),
            session_uuid=session_uuid,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent")
        )
        db.session.add(session)
        db.session.flush()
    else:
        print(f"[TRACK] Using existing session {session.id}")

    # Sanitize event data to remove sensitive information
    raw_event_data = data.get("event_data")
    sanitized_event_data = sanitize_event_data(raw_event_data)

    # Crear evento
    event = Event(
        client_id=client.id,
        session_id=session.id,
        event_type=event_type,
        event_data=sanitized_event_data
    )

    print(f"[TRACK] Saving event {event_type} for client {client.id}")
    db.session.add(event)
    db.session.commit()

    return jsonify({
        "status": "ok",
        "session_uuid": session_uuid
    }), 200

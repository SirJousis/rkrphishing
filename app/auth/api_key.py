from functools import wraps
from flask import request, jsonify
from app.models.client import Client

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = (
            request.headers.get("X-API-Key")
            or request.args.get("api_key")
            or (request.json or {}).get("api_key")
        )

        if not api_key:
            return jsonify({"error": "API key missing"}), 401

        client = Client.query.filter_by(api_key=api_key).first()
        if not client:
            return jsonify({"error": "Invalid API key"}), 403

        # Inyectamos el cliente validado
        request.client = client
        return f(*args, **kwargs)
    return decorated

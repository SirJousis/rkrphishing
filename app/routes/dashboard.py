from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.models.event import Event
from app.models.session import VisitSession
from app.models.campaign import Campaign
from app.extensions import db

dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard"
)

@dashboard_bp.route("/")
@login_required
def index():
    # Admin is redirected to their own panel or sees a global view (implemented in admin_bp usually, but here checking role)
    if current_user.role == "admin":
        from flask import redirect, url_for
        return redirect(url_for("admin.index"))

    client = current_user.client
    
    # Optional: Filter by campaign
    campaign_id = request.args.get('campaign_id')
    
    # Base query for events related to this client
    query = Event.query.filter_by(client_id=client.id)
    
    if campaign_id:
        # Need to join with Session if campaign_id is not directly on Event (it's on Session usually or passed in event_data)
        # Event -> Session. Model says Event has session_id, Session has campaign_id
        query = query.join(VisitSession).filter(VisitSession.campaign_id == campaign_id)

    # Metrics
    total_visits = query.filter_by(event_type='visit').count()
    
    # Unique visitors (distinct session_id)
    unique_visitors = query.with_entities(Event.session_id).distinct().count()
    
    credentials_captured = query.filter_by(event_type='credentials_submitted').count()
    clicks = query.filter_by(event_type='click').count()

    campaigns = Campaign.query.filter_by(client_id=client.id).all()

    return render_template(
        "dashboard/index.html",
        client=client,
        total_visits=total_visits,
        unique_visitors=unique_visitors,
        credentials_captured=credentials_captured,
        clicks=clicks,
        campaigns=campaigns,
        selected_campaign_id=int(campaign_id) if campaign_id else None
    )

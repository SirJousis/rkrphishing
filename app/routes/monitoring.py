from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.monitored_domain import MonitoredDomain
from app.models.discovered_domain import DiscoveredDomain
from app.services.domain_monitor import DomainMonitorService
from app.extensions import db

monitoring_bp = Blueprint("monitoring", __name__, url_prefix="/dashboard/monitoring")

@monitoring_bp.route("/")
@login_required
def index():
    if current_user.role == "admin":
        # Admin sees all? Or just forbidden? 
        # User request said: "los usuarios de ese cliente podrán ver los dominios unicamente de la empresa a la que pertenecen."
        # For now, let's assume admin can see everything if they belong to an org, but here we can show personal ones.
        pass
    
    client = current_user.client
    monitored_domains = MonitoredDomain.query.filter_by(client_id=client.id).all()
    return render_template("monitoring/index.html", monitored_domains=monitored_domains, client=client)

@monitoring_bp.route("/add", methods=["POST"])
@login_required
def add_domain():
    domain = request.form.get("domain")
    if not domain:
        flash("Domain is required", "error")
        return redirect(url_for("monitoring.index"))
    
    # Simple validation
    domain = domain.strip().lower()
    if domain.startswith("http://"): domain = domain[7:]
    if domain.startswith("https://"): domain = domain[8:]
    if "/" in domain: domain = domain.split("/")[0]

    client = current_user.client
    existing = MonitoredDomain.query.filter_by(client_id=client.id, domain=domain).first()
    if existing:
        flash("Domain already being monitored", "warning")
        return redirect(url_for("monitoring.index"))

    new_monitored = MonitoredDomain(client_id=client.id, domain=domain)
    db.session.add(new_monitored)
    db.session.commit()
    
    flash(f"Started monitoring {domain}", "success")
    return redirect(url_for("monitoring.index"))

@monitoring_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_domain(id):
    domain = MonitoredDomain.query.get_or_404(id)
    if domain.client_id != current_user.client_id:
        return "Unauthorized", 403
    
    db.session.delete(domain)
    db.session.commit()
    flash("Stopped monitoring domain", "success")
    return redirect(url_for("monitoring.index"))

@monitoring_bp.route("/details/<int:id>")
@login_required
def details(id):
    monitored = MonitoredDomain.query.get_or_404(id)
    if monitored.client_id != current_user.client_id:
        return "Unauthorized", 403
    
    discovered = DiscoveredDomain.query.filter_by(monitored_domain_id=id).order_by(DiscoveredDomain.discovered_at.desc()).all()
    return render_template("monitoring/details.html", monitored=monitored, discovered=discovered)

@monitoring_bp.route("/scan/<int:id>", methods=["POST"])
@login_required
def scan_now(id):
    monitored = MonitoredDomain.query.get_or_404(id)
    if monitored.client_id != current_user.client_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    new_found = DomainMonitorService.scan_domain(monitored)
    flash(f"Scan complete. Found {len(new_found)} new potential impersonations.", "info")
    return redirect(url_for("monitoring.details", id=id))

@monitoring_bp.route("/discovery/update/<int:id>", methods=["POST"])
@login_required
def update_discovery(id):
    discovery = DiscoveredDomain.query.get_or_404(id)
    if discovery.monitored_domain.client_id != current_user.client_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    status = request.form.get("status")
    if status in ["potential", "malicious", "whitelisted"]:
        discovery.status = status
        db.session.commit()
        flash(f"Domain {discovery.domain} marked as {status}", "success")
    
    return redirect(url_for("monitoring.details", id=discovery.monitored_domain_id))

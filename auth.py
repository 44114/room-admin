"""
Admin authentication — setup (first-run), login, logout.
"""

import logging
from datetime import datetime

from flask import (
    Blueprint, request, session, redirect, url_for, flash,
    render_template,
)

from config import Config
from utils import hash_password, verify_password, is_strong_password
from models import has_admin, create_admin, get_admin_by_username
from middleware import admin_required
from i18n import _

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ── Page Routes ──────────────────────────────────────────────────


@auth_bp.route("/setup")
def setup_page():
    """First-run admin creation page. Only accessible when no admin exists."""
    if has_admin():
        flash(_("success.admin_exists"), "info")
        return redirect(url_for("auth.login_page"))
    return render_template("setup.html")


@auth_bp.route("/login")
def login_page():
    """Admin login page. Redirects to setup if no admin exists."""
    if not has_admin():
        return redirect(url_for("auth.setup_page"))
    return render_template("login.html")


# ── API Routes ───────────────────────────────────────────────────


@auth_bp.route("/setup", methods=["POST"])
def setup():
    """Handle first-run admin account creation."""
    if has_admin():
        return {"error": _("error.admin_exists")}, 403

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")

    errors = []
    if not (3 <= len(username) <= 30 and username.replace("_", "").isalnum()):
        errors.append(_("error.setup_username"))
    if password != password_confirm:
        errors.append(_("error.password_mismatch"))
    if not is_strong_password(password):
        errors.append(_("error.password_weak"))

    if errors:
        flash("；".join(errors), "error")
        return redirect(url_for("auth.setup_page"))

    pwd_hash = hash_password(password)
    create_admin(username, pwd_hash)

    # Auto-login
    session.clear()
    session["admin_id"] = 1
    session["admin_username"] = username
    session.permanent = True

    logger.info("Admin account '%s' created.", username)
    flash(_("success.admin_created"), "success")
    return redirect(url_for("admin.dashboard"))


@auth_bp.route("/login", methods=["POST"])
def login():
    """Handle admin login."""
    if not has_admin():
        return redirect(url_for("auth.setup_page"))

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        flash(_("error.login_required"), "error")
        return redirect(url_for("auth.login_page"))

    import time
    time.sleep(0.5)  # Brute-force delay

    admin = get_admin_by_username(username)
    if not admin:
        # Dummy verification to mask timing
        verify_password(password, "$argon2id$v=19$m=65536,t=3,p=4$dummy$dummy")
        flash(_("error.login_invalid"), "error")
        return redirect(url_for("auth.login_page"))

    if not verify_password(password, admin["password_hash"]):
        flash(_("error.login_invalid"), "error")
        return redirect(url_for("auth.login_page"))

    session.clear()
    session["admin_id"] = admin["id"]
    session["admin_username"] = admin["username"]
    session.permanent = True

    logger.info("Admin '%s' logged in.", username)
    return redirect(url_for("admin.dashboard"))


@auth_bp.route("/logout", methods=["POST"])
@admin_required
def logout():
    """Handle admin logout."""
    session.clear()
    flash(_("success.logout"), "info")
    return redirect(url_for("auth.login_page"))

"""
Security middleware: admin auth decorator, CSRF, headers.
"""

from functools import wraps

from flask import session, redirect, url_for, flash


def admin_required(f):
    """Decorator: require admin login."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_id"):
            flash("请先登录管理员账号。", "warning")
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)

    return decorated


def setup_security_headers(app):
    """Add security headers to every response."""

    @app.after_request
    def add_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "frame-src 'none'"
        )
        return response

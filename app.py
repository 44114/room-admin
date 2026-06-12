#!/usr/bin/env python3
"""
Chat Room Admin Panel — Python Flask

A lightweight admin dashboard for the Chat Room application.
Manages users, messages, and files.

Usage:
    # Set required environment variables, then:
    python app.py

    Admin panel runs on http://127.0.0.1:9889 by default.
    Do NOT expose this port to the public internet.
"""

import logging
import sys

from flask import Flask, session, redirect, url_for, flash, render_template

from config import Config
from models import init_db, has_admin
from middleware import setup_security_headers, admin_required
from auth import auth_bp
from admin import admin_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)

    # Flask config
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["SESSION_COOKIE_HTTPONLY"] = Config.SESSION_COOKIE_HTTPONLY
    app.config["SESSION_COOKIE_SAMESITE"] = Config.SESSION_COOKIE_SAMESITE
    app.config["SESSION_COOKIE_SECURE"] = Config.SESSION_COOKIE_SECURE
    app.config["PERMANENT_SESSION_LIFETIME"] = Config.PERMANENT_SESSION_LIFETIME

    # Security
    setup_security_headers(app)

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # ── Routes ─────────────────────────────────────────────────

    @app.route("/")
    def index():
        if not has_admin():
            return redirect(url_for("auth.setup_page"))
        if session.get("admin_id"):
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("auth.login_page"))

    @app.errorhandler(404)
    def not_found(e):
        return "<h1>404</h1><p>页面不存在</p>", 404

    @app.errorhandler(500)
    def server_error(e):
        return "<h1>500</h1><p>服务器错误</p>", 500

    return app


if __name__ == "__main__":
    app = create_app()

    # Initialize the admin_users table
    try:
        init_db()
        logger.info("数据库初始化完成。")
    except Exception as e:
        logger.error("数据库初始化失败：%s", e)
        logger.error("请确认 MySQL 环境变量设置正确。")
        sys.exit(1)

    if has_admin():
        logger.info("管理面板已就绪。")
    else:
        logger.info("首次运行 — 请访问 http://%s:%d/auth/setup 创建管理员账号。",
                    Config.HOST, Config.PORT)

    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
    )

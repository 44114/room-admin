"""
Admin management routes — dashboard, user management, message management.
"""

import logging

from flask import (
    Blueprint, request, session, redirect, url_for, flash,
    render_template, jsonify,
)

from middleware import admin_required
from utils import get_db

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__)


# ── Dashboard ─────────────────────────────────────────────────────


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    """Main admin dashboard with overview stats."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM users WHERE is_active = TRUE")
            active_users = cur.fetchone()["cnt"]

            cur.execute("SELECT COUNT(*) AS cnt FROM users WHERE is_active = FALSE")
            deleted_users = cur.fetchone()["cnt"]

            cur.execute("SELECT COUNT(*) AS cnt FROM messages")
            total_messages = cur.fetchone()["cnt"]

            cur.execute("SELECT COUNT(*) AS cnt FROM files WHERE upload_complete = TRUE")
            total_files = cur.fetchone()["cnt"]
    finally:
        conn.close()

    return render_template(
        "dashboard.html",
        username=session.get("admin_username"),
        stats={
            "active_users": active_users,
            "deleted_users": deleted_users,
            "total_messages": total_messages,
            "total_files": total_files,
        },
    )


# ── User Management ───────────────────────────────────────────────


@admin_bp.route("/users")
@admin_required
def user_list():
    """List all users."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, is_active, created_at FROM users ORDER BY id DESC"
            )
            users = cur.fetchall()
    finally:
        conn.close()

    return render_template("user_list.html", users=users)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    """Soft-delete a user (set is_active = FALSE)."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET is_active = FALSE WHERE id = %s",
                (user_id,),
            )
            affected = cur.rowcount
        conn.commit()

        if affected:
            logger.info("Admin deleted user %d.", user_id)
            flash(f"用户 #{user_id} 已被禁用。", "success")
        else:
            flash("用户不存在。", "error")
    except Exception as e:
        conn.rollback()
        flash(f"操作失败：{e}", "error")
    finally:
        conn.close()

    return redirect(url_for("admin.user_list"))


@admin_bp.route("/users/<int:user_id>/activate", methods=["POST"])
@admin_required
def activate_user(user_id):
    """Re-activate a soft-deleted user."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET is_active = TRUE WHERE id = %s",
                (user_id,),
            )
            affected = cur.rowcount
        conn.commit()

        if affected:
            flash(f"用户 #{user_id} 已恢复。", "success")
        else:
            flash("用户不存在。", "error")
    except Exception as e:
        conn.rollback()
        flash(f"操作失败：{e}", "error")
    finally:
        conn.close()

    return redirect(url_for("admin.user_list"))


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@admin_required
def reset_user_password(user_id):
    """Reset a user's password to a random token (force re-login)."""
    import secrets
    from utils import hash_password

    new_pwd = secrets.token_hex(16)
    new_hash = hash_password(new_pwd)

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (new_hash, user_id),
            )
            affected = cur.rowcount
        conn.commit()

        if affected:
            flash(
                f"用户 #{user_id} 密码已重置为：{new_pwd} （请将此密码告知用户，登录后立即修改）",
                "success",
            )
            logger.info("Admin reset password for user %d.", user_id)
        else:
            flash("用户不存在。", "error")
    except Exception as e:
        conn.rollback()
        flash(f"操作失败：{e}", "error")
    finally:
        conn.close()

    return redirect(url_for("admin.user_list"))


# ── Message Management ────────────────────────────────────────────


@admin_bp.route("/messages")
@admin_required
def message_list():
    """List all messages with pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM messages")
            total = cur.fetchone()["cnt"]

            cur.execute(
                """SELECT m.id, m.content, m.room, m.created_at,
                          u.username AS sender_name
                   FROM messages m
                   LEFT JOIN users u ON m.sender_id = u.id
                   ORDER BY m.id DESC
                   LIMIT %s OFFSET %s""",
                (per_page, offset),
            )
            messages = cur.fetchall()
    finally:
        conn.close()

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "message_list.html",
        messages=messages,
        page=page,
        total_pages=total_pages,
        total=total,
    )


@admin_bp.route("/messages/<int:msg_id>/delete", methods=["POST"])
@admin_required
def delete_message(msg_id):
    """Delete a single message."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM messages WHERE id = %s", (msg_id,))
            affected = cur.rowcount
        conn.commit()

        if affected:
            flash(f"消息 #{msg_id} 已删除。", "success")
        else:
            flash("消息不存在。", "error")
    except Exception as e:
        conn.rollback()
        flash(f"操作失败：{e}", "error")
    finally:
        conn.close()

    return redirect(url_for("admin.message_list"))


@admin_bp.route("/messages/clear", methods=["POST"])
@admin_required
def clear_messages():
    """Delete ALL messages (dangerous — requires confirmation)."""
    confirmation = request.form.get("confirm", "")
    if confirmation != "DELETE ALL MESSAGES":
        flash("请输入确认短语 'DELETE ALL MESSAGES' 以执行此操作。", "error")
        return redirect(url_for("admin.message_list"))

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM messages")
            deleted = cur.rowcount
        conn.commit()

        flash(f"已清空全部聊天记录（{deleted} 条）。", "success")
        logger.warning("Admin cleared all %d messages.", deleted)
    except Exception as e:
        conn.rollback()
        flash(f"操作失败：{e}", "error")
    finally:
        conn.close()

    return redirect(url_for("admin.message_list"))


# ── File Overview ─────────────────────────────────────────────────


@admin_bp.route("/files")
@admin_required
def file_list():
    """List all uploaded files."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT f.id, f.filename, f.file_size, f.mime_type,
                          f.upload_complete, f.created_at,
                          u.username AS uploader_name
                   FROM files f
                   LEFT JOIN users u ON f.uploader_id = u.id
                   ORDER BY f.id DESC"""
            )
            files = cur.fetchall()
    finally:
        conn.close()

    return render_template("file_list.html", files=files)

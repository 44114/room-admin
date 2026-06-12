"""
Database initialization — creates the admin_users table if missing.
All other tables (users, messages, files, etc.) already exist from the main app.
"""

import logging

from utils import get_db

logger = logging.getLogger(__name__)

CREATE_ADMIN_TABLE = """
CREATE TABLE IF NOT EXISTS admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


def init_db():
    """Ensure the admin_users table exists."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_ADMIN_TABLE)
        conn.commit()
        logger.info("Admin database ready.")
    finally:
        conn.close()


def has_admin() -> bool:
    """Check if any admin account exists (controls first-run setup)."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM admin_users")
            return cur.fetchone()["cnt"] > 0
    finally:
        conn.close()


def create_admin(username: str, password_hash: str) -> None:
    """Create the first (or only) admin account."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO admin_users (username, password_hash) VALUES (%s, %s)",
                (username, password_hash),
            )
        conn.commit()
    finally:
        conn.close()


def get_admin_by_username(username: str) -> dict | None:
    """Fetch admin user record by username."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, password_hash FROM admin_users WHERE username = %s",
                (username,),
            )
            return cur.fetchone()
    finally:
        conn.close()

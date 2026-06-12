"""
Configuration — all sensitive values read from environment variables.
Never hardcode credentials.
"""

import os
import secrets


class Config:
    # Flask
    SECRET_KEY: str = os.environ.get("SECRET_KEY", secrets.token_hex(64))

    # MySQL (connects to the SAME database as the main chat room)
    MYSQL_HOST: str = os.environ.get("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT: int = int(os.environ.get("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.environ.get("MYSQL_USER", "chatroom")
    MYSQL_PASSWORD: str = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DB: str = os.environ.get("MYSQL_DB", "chatroom")

    # Session
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    SESSION_COOKIE_SECURE: bool = False
    PERMANENT_SESSION_LIFETIME: int = 1800

    # Argon2id
    ARGON2_TIME_COST: int = 3
    ARGON2_MEMORY_COST: int = 65536
    ARGON2_PARALLELISM: int = 4
    ARGON2_HASH_LENGTH: int = 32
    ARGON2_SALT_LENGTH: int = 16

    # Server
    HOST: str = "127.0.0.1"  # admin panel should NOT be exposed to public
    PORT: int = int(os.environ.get("ADMIN_PORT", "9889"))
    DEBUG: bool = os.environ.get("FLASK_DEBUG", "0") == "1"

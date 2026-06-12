"""
Utilities: password hashing, DB connection, validators.
"""

import hmac
import logging
import re

import pymysql
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError

from config import Config

logger = logging.getLogger(__name__)

_ph = PasswordHasher(
    time_cost=Config.ARGON2_TIME_COST,
    memory_cost=Config.ARGON2_MEMORY_COST,
    parallelism=Config.ARGON2_PARALLELISM,
    hash_len=Config.ARGON2_HASH_LENGTH,
    salt_len=Config.ARGON2_SALT_LENGTH,
)


def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against an Argon2id hash (constant time)."""
    try:
        return _ph.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def constant_time_compare(a: str, b: str) -> bool:
    """Compare two strings in constant time."""
    return hmac.compare_digest(a.encode(), b.encode())


def is_strong_password(password: str) -> bool:
    """Check password strength: 8+ chars, 3+ of 4 character types."""
    if not password or len(password) < 8 or len(password) > 128:
        return False
    return (
        bool(re.search(r"[A-Z]", password))
        + bool(re.search(r"[a-z]", password))
        + bool(re.search(r"[0-9]", password))
        + bool(re.search(r"[^A-Za-z0-9]", password))
    ) >= 3


def get_db():
    """Get a PyMySQL connection."""
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )

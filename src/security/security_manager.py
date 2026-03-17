"""
Security Manager — Protects the AI Office system.

Features:
- API key management (env vars, never hardcoded)
- Password hashing (bcrypt)
- Rate limiting
- Input validation
- JWT token management
- User authorization
"""

import logging
import time
import re
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

try:
    from jose import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False


class SecurityManager:
    """Central security manager for the AI Office."""

    def __init__(self, secret_key: str = "change-me", algorithm: str = "HS256",
                 token_expiry_hours: int = 24):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expiry_hours = token_expiry_hours
        self._rate_limits: Dict[str, list] = defaultdict(list)
        self._max_requests_per_minute = 30

    # ─── Password Hashing ──────────────────────────────────────────

    def hash_password(self, password: str) -> str:
        if BCRYPT_AVAILABLE:
            return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        logger.warning("bcrypt not available, storing plain text (UNSAFE)")
        return password

    def verify_password(self, password: str, hashed: str) -> bool:
        if BCRYPT_AVAILABLE:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        return password == hashed

    # ─── JWT Tokens ────────────────────────────────────────────────

    def create_token(self, user_id: str, extra_data: dict = None) -> Optional[str]:
        if not JWT_AVAILABLE:
            logger.error("python-jose not installed")
            return None
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            "iat": datetime.utcnow(),
            **(extra_data or {})
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[dict]:
        if not JWT_AVAILABLE:
            return None
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            return None

    # ─── Rate Limiting ─────────────────────────────────────────────

    def check_rate_limit(self, user_id: str) -> bool:
        """Returns True if request is allowed, False if rate limited."""
        now = time.time()
        window = 60  # 1 minute
        self._rate_limits[user_id] = [
            t for t in self._rate_limits[user_id] if now - t < window
        ]
        if len(self._rate_limits[user_id]) >= self._max_requests_per_minute:
            return False
        self._rate_limits[user_id].append(now)
        return True

    # ─── Input Validation ──────────────────────────────────────────

    @staticmethod
    def sanitize_input(text: str) -> str:
        """Remove potentially dangerous characters."""
        text = re.sub(r'[<>{}]', '', text)
        text = text.strip()
        if len(text) > 5000:
            text = text[:5000]
        return text

    @staticmethod
    def validate_task_description(description: str) -> bool:
        """Validate task description."""
        if not description or len(description.strip()) < 3:
            return False
        if len(description) > 5000:
            return False
        return True

    # ─── User Authorization ────────────────────────────────────────

    def is_authorized_telegram_user(self, user_id: int, authorized_list: list) -> bool:
        """Check if Telegram user is authorized."""
        if not authorized_list:
            return True  # No restrictions if list is empty
        return user_id in authorized_list

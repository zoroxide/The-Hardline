import hmac
import hashlib
from typing import Optional
from fastapi import Response, Request

from app.config import SECRET_KEY, COOKIE_NAME, COOKIE_MAX_AGE, ADMIN_USERS
from app.models.auth import SessionUser

class AuthController:
    """Controller handling authentication, session tokens, and security checks."""

    @staticmethod
    def sign_session_token(username: str) -> str:
        """Create a tamper-proof HMAC-SHA256 signed session cookie value."""
        signature = hmac.new(
            SECRET_KEY.encode("utf-8"),
            username.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return f"{username}.{signature}"

    @staticmethod
    def verify_session_token(token: Optional[str]) -> Optional[SessionUser]:
        """Verify the integrity of a signed session token."""
        if not token or "." not in token:
            return None
        try:
            username, signature = token.rsplit(".", 1)
            expected_sig = hmac.new(
                SECRET_KEY.encode("utf-8"),
                username.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            if hmac.compare_digest(signature, expected_sig):
                return SessionUser(username=username)
        except Exception:
            return None
        return None

    @classmethod
    def get_current_user(cls, request: Request) -> Optional[SessionUser]:
        """Extract and validate the session user from request cookies."""
        cookie_val = request.cookies.get(COOKIE_NAME)
        return cls.verify_session_token(cookie_val)

    @classmethod
    def authenticate_credentials(cls, username: str, password: str) -> bool:
        """Validate provided username and password against configured accounts."""
        u_clean = username.strip()
        p_clean = password.strip()
        expected_pass = ADMIN_USERS.get(u_clean)
        if not expected_pass:
            return False
        return hmac.compare_digest(p_clean, expected_pass)

    @classmethod
    def set_auth_cookie(cls, response: Response, username: str) -> None:
        """Attach signed authentication cookie to HTTP response."""
        token = cls.sign_session_token(username)
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            path="/"
        )

    @classmethod
    def clear_auth_cookie(cls, response: Response) -> None:
        """Remove authentication cookie from HTTP response."""
        response.delete_cookie(key=COOKIE_NAME, path="/")

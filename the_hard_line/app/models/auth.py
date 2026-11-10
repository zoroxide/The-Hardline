from typing import Optional
from pydantic import BaseModel

class SessionUser(BaseModel):
    """Domain model representing an authenticated user session."""
    username: str
    is_authenticated: bool = True

class LoginCredentials(BaseModel):
    """Data model representing submitted login credentials."""
    username: str
    password: str

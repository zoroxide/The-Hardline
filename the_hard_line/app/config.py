import os
from pathlib import Path
from typing import Dict

BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DB_HOST: str = os.getenv("DB_HOST", "postgres-egypt")
DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
DB_USER: str = os.getenv("DB_USER", "loay")
DB_PASS: str = os.getenv("DB_PASS", "2004")
DB_NAME: str = os.getenv("DB_NAME", "egypt_users")

# Application Security
SECRET_KEY: str = os.getenv("SECRET_KEY", "TheHardlineSecretKeyForSessionSecurity2026")
COOKIE_NAME: str = "session"
COOKIE_MAX_AGE: int = 86400 * 7  # 7 days

# Authentication credentials store
ADMIN_USERS: Dict[str, str] = {
    "admin": "1234@QWer",
    "loay": "2004"
}
if os.getenv("ADMIN_USER") and os.getenv("ADMIN_PASS"):
    ADMIN_USERS[os.getenv("ADMIN_USER")] = os.getenv("ADMIN_PASS")

# Directories
TEMPLATES_DIR: Path = BASE_DIR / "templates"
STATIC_DIR: Path = BASE_DIR / "static"

# Search configuration
MAX_RESULTS_LIMIT: int = 50

# FlareSolverr / External Scraper endpoint
FLARESOLVERR_URL: str = os.getenv("FLARESOLVERR_URL", "http://192.168.1.201:8191/v1")

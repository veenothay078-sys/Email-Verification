import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load .env from backend folder or root folder
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
root_env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
elif root_env_path.exists():
    load_dotenv(dotenv_path=root_env_path, override=True)
else:
    load_dotenv(override=True)

class Settings:
    PROJECT_NAME: str = "OpenMail Verify API"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./verification_history.db")
    
    # History tracking toggle
    ENABLE_HISTORY_LOGGING: bool = os.getenv("ENABLE_HISTORY_LOGGING", "true").lower() in ("true", "1", "yes")
    
    # DNS configuration & Caching
    DNS_TIMEOUT_SECONDS: float = float(os.getenv("DNS_TIMEOUT_SECONDS", "3.0"))
    DNS_LIFETIME_SECONDS: float = float(os.getenv("DNS_LIFETIME_SECONDS", "5.0"))
    DNS_CACHE_TTL_SECONDS: int = int(os.getenv("DNS_CACHE_TTL_SECONDS", "300"))
    
    # Batch verification & Document Upload limits
    MAX_BATCH_SIZE: int = int(os.getenv("MAX_BATCH_SIZE", "100"))
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    MAX_BULK_EMAILS: int = int(os.getenv("MAX_BULK_EMAILS", "100"))
    BULK_CONCURRENCY: int = int(os.getenv("BULK_CONCURRENCY", "3"))
    
    # Technical SMTP Probe configuration (Non-delivery verification)
    SMTP_TIMEOUT_SECONDS: float = float(os.getenv("SMTP_TIMEOUT_SECONDS", "3.0"))
    SMTP_HELO_DOMAIN: str = os.getenv("SMTP_HELO_DOMAIN", "mailscope.io")
    VERIFIER_MAIL_FROM: str = os.getenv("VERIFIER_MAIL_FROM", "verify@mailscope.io")
    DEV_MODE_SIMULATE_SMTP: bool = False

    # Optional External Verification Provider Adapter
    EXTERNAL_VERIFIER_ENABLED: bool = os.getenv("EXTERNAL_VERIFIER_ENABLED", "false").lower() in ("true", "1", "yes")
    EXTERNAL_VERIFIER_URL: str = os.getenv("EXTERNAL_VERIFIER_URL", "")
    EXTERNAL_VERIFIER_API_KEY: str = os.getenv("EXTERNAL_VERIFIER_API_KEY", "")

settings = Settings()

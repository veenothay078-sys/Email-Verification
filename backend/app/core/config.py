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
    
    # DNS configuration
    DNS_TIMEOUT_SECONDS: float = float(os.getenv("DNS_TIMEOUT_SECONDS", "3.0"))
    DNS_LIFETIME_SECONDS: float = float(os.getenv("DNS_LIFETIME_SECONDS", "5.0"))
    
    # Batch verification limit
    MAX_BATCH_SIZE: int = int(os.getenv("MAX_BATCH_SIZE", "50"))
    
    # Mailbox Verification / OTP Configuration
    OTP_EXPIRATION_SECONDS: int = int(os.getenv("OTP_EXPIRATION_SECONDS", "600"))  # 10 minutes
    OTP_MAX_ATTEMPTS: int = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
    OTP_RESEND_COOLDOWN_SECONDS: int = int(os.getenv("OTP_RESEND_COOLDOWN_SECONDS", "60")) # 60 seconds
    
    # Outbound SMTP Delivery Configuration (for sending real confirmation emails)
    SMTP_HOST: str = os.getenv("SMTP_HOST") or os.getenv("SMTP_SERVER") or ""
    SMTP_PORT: int = int(os.getenv("SMTP_PORT") or "587")
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER") or ""
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS") or ""
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL") or os.getenv("SMTP_FROM") or os.getenv("SMTP_SENDER") or os.getenv("SMTP_USERNAME") or "noreply@openmail.verify"
    SMTP_USE_TLS: bool = str(os.getenv("SMTP_USE_TLS", os.getenv("SMTP_STARTTLS", "true"))).lower() in ("true", "1", "yes")
    SMTP_USE_SSL: bool = str(os.getenv("SMTP_USE_SSL", "false")).lower() in ("true", "1", "yes")

settings = Settings()

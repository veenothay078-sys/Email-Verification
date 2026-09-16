from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, JSON
from datetime import datetime
from app.core.database import Base

class VerificationHistory(Base):
    __tablename__ = "verification_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), index=True, nullable=False)
    normalized_email = Column(String(255), nullable=False)
    domain = Column(String(255), index=True, nullable=False)
    status = Column(String(50), index=True, nullable=False) # VALID, INVALID, RISKY, UNKNOWN
    score = Column(Integer, nullable=False)
    is_syntax_valid = Column(Boolean, default=False)
    is_domain_resolved = Column(Boolean, default=False)
    is_mx_found = Column(Boolean, default=False)
    is_disposable = Column(Boolean, default=False)
    is_role_based = Column(Boolean, default=False)
    is_free_provider = Column(Boolean, default=False)
    message = Column(String(500), nullable=False)
    checks_detail = Column(JSON, nullable=True) # Full structured checks object
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

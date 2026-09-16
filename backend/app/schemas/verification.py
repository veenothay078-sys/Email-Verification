from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class VerifyRequest(BaseModel):
    email: str = Field(..., description="Email address to verify", json_schema_extra={"example": "user@example.com"})

class BatchVerifyRequest(BaseModel):
    emails: List[str] = Field(..., description="List of email addresses (up to 50)", max_length=50)

class CheckDetail(BaseModel):
    passed: bool
    status: str # "PASS", "FAIL", "UNKNOWN", "warning", "info", "passed", "failed"
    message: str
    display_value: Optional[str] = None # e.g. "PASS", "FAIL", "ACCEPTED", "REJECTED", "BLOCKED", "TIMEOUT", "CONFIRMED", "UNCONFIRMED", "YES", "NO"
    details: Optional[Dict[str, Any]] = None

class DomainIntelligence(BaseModel):
    domain: str
    is_resolvable: bool
    mx_records: List[Dict[str, Any]] = []
    a_records: List[str] = []
    is_disposable: bool
    is_free_provider: bool
    is_catch_all: bool = False
    has_mail_server: bool
    smtp_verified: bool = False
    smtp_status: str = "UNKNOWN"
    mailbox_status: str = "UNCONFIRMED"

class VerificationChecks(BaseModel):
    syntax: CheckDetail
    domain: CheckDetail
    dns: CheckDetail
    mx: CheckDetail
    smtp: CheckDetail
    mailbox: CheckDetail
    disposable: CheckDetail
    role_based: CheckDetail
    free_provider: CheckDetail
    catch_all: Optional[CheckDetail] = None

class VerifyResponse(BaseModel):
    email: str
    normalized_email: str
    domain: str
    status: str # "VALID", "INVALID", "RISKY", "UNKNOWN"
    score: int # 0 to 100
    confidence: int # 0 to 100
    checks: VerificationChecks
    domain_intelligence: Optional[DomainIntelligence] = None
    message: str
    reason: str
    verified_at: datetime = Field(default_factory=datetime.utcnow)

class BatchVerifyResponse(BaseModel):
    total: int
    valid_count: int
    invalid_count: int
    risky_count: int
    unknown_count: int
    average_score: float
    results: List[VerifyResponse]

class HistoryItem(BaseModel):
    id: int
    email: str
    normalized_email: str
    domain: str
    status: str
    score: int
    is_syntax_valid: bool
    is_domain_resolved: bool
    is_mx_found: bool
    is_disposable: bool
    is_role_based: bool
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class HistoryListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[HistoryItem]

class StatsSummary(BaseModel):
    total_verified: int
    valid_count: int
    invalid_count: int
    risky_count: int
    unknown_count: int
    valid_rate: float
    average_score: float
    recent_activity: List[Dict[str, Any]] = []

class SendMailboxCodeRequest(BaseModel):
    email: str = Field(..., description="Email address to send the verification code to")

class SendMailboxCodeResponse(BaseModel):
    success: bool
    message: str
    expires_in_seconds: int = 600
    cooldown_seconds: int = 60
    delivery_mode: str = "dev_simulated"

class VerifyMailboxCodeRequest(BaseModel):
    email: str = Field(..., description="Target email address")
    code: str = Field(..., description="6-digit verification code entered by the user", min_length=6, max_length=6)

class VerifyMailboxCodeResponse(BaseModel):
    success: bool
    message: str
    verification_result: Optional[VerifyResponse] = None
    attempts_remaining: Optional[int] = None

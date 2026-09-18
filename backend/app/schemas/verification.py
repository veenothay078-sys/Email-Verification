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

class SMTPStageDetails(BaseModel):
    status_code: Optional[int] = None
    code: Optional[int] = None
    response: Optional[str] = None

class SMTPTrace(BaseModel):
    attempted: bool = False
    connected: bool = False
    hostname: Optional[str] = None
    mx_host: Optional[str] = None
    port: int = 25
    stage: str = "SKIPPED" # CONNECT, GREETING, EHLO, MAIL_FROM, RCPT_TO, CATCH_ALL, SKIPPED, ERROR
    greeting: Optional[SMTPStageDetails] = None
    ehlo: Optional[SMTPStageDetails] = None
    mail_from: Optional[SMTPStageDetails] = None
    rcpt_to: Optional[SMTPStageDetails] = None
    data_sent: bool = False
    catch_all_probe: Optional[Dict[str, Any]] = None
    attempted_servers: List[Dict[str, Any]] = []

class VerifyResponse(BaseModel):
    email: str
    normalized_email: str
    domain: str
    status: str # "VALID", "INVALID", "RISKY", "UNKNOWN"
    final_status: str # "REAL / REACHABLE", "NOT REAL / INVALID", "RISKY", "UNKNOWN"
    classification: str = "UNKNOWN" # "REAL", "INVALID", "UNKNOWN", "RISKY"
    score: int # 0 to 100
    confidence: int # 0 to 100
    confidence_level: str = "HIGH" # "HIGH", "MEDIUM", "LOW"
    verification_method: str = "NON_CONTACT_SMTP"
    notification_sent: bool = False
    data_sent: bool = False
    
    # Explicit 5-Step Evidence Fields
    email_format: str = "VALID" # VALID or INVALID
    domain_status: str = "VALID" # VALID, INVALID, UNKNOWN
    mx_status: str = "FOUND" # FOUND, MISSING, UNKNOWN
    smtp_connection_status: str = "CONNECTED" # CONNECTED, BLOCKED, TIMEOUT, SKIPPED
    recipient_status: str = "UNCONFIRMED" # ACCEPTED, REJECTED, UNCONFIRMED, CATCH_ALL

    # Internal Evidence & Capability Fields
    syntax_valid: bool = True
    domain_exists: bool = True
    dns_resolved: bool = True
    mx_found: bool = True
    mx_host: Optional[str] = None
    smtp_connection: bool = False
    smtp_recipient_response: Optional[str] = None
    mailbox_evidence: str = "NO_EVIDENCE" # CONFIRMED_EXISTS, CONFIRMED_REJECTED, ACCEPTED_NOT_CONFIRMED, PROVIDER_BLOCKED, CATCH_ALL, TIMEOUT, AMBIGUOUS, NO_EVIDENCE
    verification_capability: str = "UNKNOWN" # MAILBOX_VERIFICATION_SUPPORTED, MAILBOX_VERIFICATION_BLOCKED, MAILBOX_VERIFICATION_AMBIGUOUS, CATCH_ALL, UNKNOWN
    mailbox_existence: str = "NOT CONFIRMED" # CONFIRMED, REJECTED, NOT CONFIRMED
    catch_all_detected: bool = False
    disposable_detected: bool = False
    role_account_detected: bool = False
    risk_signals: List[str] = []

    performance_metrics: Optional[Dict[str, float]] = None
    smtp: Optional[Dict[str, Any]] = None
    smtp_trace: Optional[Dict[str, Any]] = None
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
    total_batch_time_ms: Optional[float] = None
    average_verification_time_ms: Optional[float] = None
    emails_per_second: Optional[float] = None
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

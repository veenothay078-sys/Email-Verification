from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.schemas.verification import (
    VerifyRequest,
    BatchVerifyRequest,
    VerifyResponse,
    BatchVerifyResponse,
    HistoryListResponse,
    HistoryItem,
    StatsSummary,
    SendMailboxCodeRequest,
    SendMailboxCodeResponse,
    VerifyMailboxCodeRequest,
    VerifyMailboxCodeResponse,
)
from app.services.verification_service import verification_service
from app.services.mailbox_challenge_service import mailbox_challenge_service
from app.services.history_service import history_service
from app.core.config import settings

router = APIRouter()

@router.get("/health", summary="Health Check")
def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME, "version": settings.PROJECT_VERSION}

@router.post("/verify", response_model=VerifyResponse, summary="Verify single email address")
def verify_email(
    payload: VerifyRequest,
    db: Session = Depends(get_db)
):
    if not payload.email or not payload.email.strip():
        raise HTTPException(status_code=400, detail="Email address field is required.")
    
    result = verification_service.verify_email(payload.email.strip())
    
    # Store in history
    history_service.record_verification(db, result)
    
    return result

@router.post("/verify/batch", response_model=BatchVerifyResponse, summary="Batch verify up to 50 email addresses")
def batch_verify_emails(
    payload: BatchVerifyRequest,
    db: Session = Depends(get_db)
):
    raw_emails = payload.emails
    if not raw_emails:
        raise HTTPException(status_code=400, detail="Email list cannot be empty.")
    
    # Enforce limit
    if len(raw_emails) > settings.MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size exceeds maximum limit of {settings.MAX_BATCH_SIZE} emails."
        )
    
    results: List[VerifyResponse] = []
    valid_c = 0
    invalid_c = 0
    risky_c = 0
    unknown_c = 0
    total_score = 0

    for email_str in raw_emails:
        cleaned = email_str.strip()
        if not cleaned:
            continue
        res = verification_service.verify_email(cleaned)
        results.append(res)
        history_service.record_verification(db, res)
        
        if res.status == "VALID":
            valid_c += 1
        elif res.status == "INVALID":
            invalid_c += 1
        elif res.status == "RISKY":
            risky_c += 1
        else:
            unknown_c += 1
            
        total_score += res.score

    total = len(results)
    avg_score = round(total_score / total, 1) if total > 0 else 0.0

    return BatchVerifyResponse(
        total=total,
        valid_count=valid_c,
        invalid_count=invalid_c,
        risky_count=risky_c,
        unknown_count=unknown_c,
        average_score=avg_score,
        results=results,
    )

@router.get("/history", response_model=HistoryListResponse, summary="Get verification history")
def get_verification_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (VALID, INVALID, RISKY, UNKNOWN)"),
    search: Optional[str] = Query(None, description="Search query by email or domain"),
    db: Session = Depends(get_db)
):
    skip = (page - 1) * page_size
    total, items = history_service.get_history(
        db=db,
        skip=skip,
        limit=page_size,
        status=status,
        search=search,
    )
    
    # Map to schema
    history_items = [HistoryItem.model_validate(item) for item in items]
    
    return HistoryListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=history_items,
    )

@router.delete("/history", summary="Clear verification history")
def clear_verification_history(db: Session = Depends(get_db)):
    deleted_count = history_service.clear_history(db)
    return {"message": f"Successfully cleared {deleted_count} history records.", "deleted": deleted_count}

@router.get("/stats", response_model=StatsSummary, summary="Get verification statistics summary")
def get_stats(db: Session = Depends(get_db)):
    return history_service.get_stats(db)

@router.post("/mailbox/send-code", response_model=SendMailboxCodeResponse, summary="Send one-time mailbox verification code")
def send_mailbox_verification_code(payload: SendMailboxCodeRequest):
    email = payload.email.strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email address is required.")
    
    res = mailbox_challenge_service.generate_and_send_code(email)
    if not res.get("success"):
        raise HTTPException(
            status_code=res.get("status_code", 400),
            detail=res.get("error", "Unable to send verification code.")
        )
    
    return SendMailboxCodeResponse(
        success=True,
        message=res["message"],
        expires_in_seconds=res.get("expires_in_seconds", 600),
        cooldown_seconds=res.get("cooldown_seconds", 60),
        delivery_mode=res.get("delivery_mode", "dev_simulated")
    )

@router.post("/mailbox/verify-code", response_model=VerifyMailboxCodeResponse, summary="Verify mailbox code and confirm ownership")
def verify_mailbox_code(
    payload: VerifyMailboxCodeRequest,
    db: Session = Depends(get_db)
):
    email = payload.email.strip()
    code = payload.code.strip()
    
    if not email or not code:
        raise HTTPException(status_code=400, detail="Email and 6-digit verification code are required.")
    
    res = mailbox_challenge_service.verify_code(email, code)
    if not res.get("success"):
        raise HTTPException(
            status_code=res.get("status_code", 400),
            detail=res.get("error", "Invalid verification code.")
        )
    
    # Re-verify email now that mailbox ownership is confirmed
    updated_result = verification_service.verify_email(email)
    
    # Record updated verified result in history
    history_service.record_verification(db, updated_result)
    
    return VerifyMailboxCodeResponse(
        success=True,
        message=res["message"],
        verification_result=updated_result,
        attempts_remaining=res.get("attempts_remaining")
    )

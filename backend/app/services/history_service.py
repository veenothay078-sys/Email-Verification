from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional, Dict, Any
from app.models.verification import VerificationHistory
from app.schemas.verification import VerifyResponse, StatsSummary
from app.core.config import settings

class HistoryService:
    def record_verification(self, db: Session, res: VerifyResponse) -> Optional[VerificationHistory]:
        """Save verification to database if history logging is enabled."""
        if not settings.ENABLE_HISTORY_LOGGING:
            return None
        
        try:
            entry = VerificationHistory(
                email=res.email,
                normalized_email=res.normalized_email,
                domain=res.domain or "unknown",
                status=res.status,
                score=res.score,
                is_syntax_valid=res.checks.syntax.passed,
                is_domain_resolved=res.checks.domain.passed and res.checks.dns.passed,
                is_mx_found=res.checks.mx.passed,
                is_disposable=not res.checks.disposable.passed,
                is_role_based=not res.checks.role_based.passed,
                is_free_provider=res.checks.free_provider.details.get("is_free_provider", False) if res.checks.free_provider.details else False,
                message=res.message,
                checks_detail=res.model_dump()["checks"],
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)
            return entry
        except Exception as e:
            db.rollback()
            # History logging error should not break the verification response
            return None

    def get_history(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple:
        query = db.query(VerificationHistory)
        
        if status and status.upper() != "ALL":
            query = query.filter(VerificationHistory.status == status.upper())
            
        if search:
            search_clean = f"%{search.strip().lower()}%"
            query = query.filter(
                (func.lower(VerificationHistory.email).like(search_clean)) |
                (func.lower(VerificationHistory.domain).like(search_clean))
            )
            
        total = query.count()
        items = query.order_by(desc(VerificationHistory.created_at)).offset(skip).limit(limit).all()
        return total, items

    def clear_history(self, db: Session) -> int:
        """Deletes all verification history logs."""
        try:
            num_rows = db.query(VerificationHistory).delete()
            db.commit()
            return num_rows
        except Exception:
            db.rollback()
            return 0

    def get_stats(self, db: Session) -> StatsSummary:
        """Calculates real aggregation statistics from database entries."""
        total = db.query(VerificationHistory).count()
        if total == 0:
            return StatsSummary(
                total_verified=0,
                valid_count=0,
                invalid_count=0,
                risky_count=0,
                unknown_count=0,
                valid_rate=0.0,
                average_score=0.0,
                recent_activity=[],
            )

        valid = db.query(VerificationHistory).filter(VerificationHistory.status == "VALID").count()
        invalid = db.query(VerificationHistory).filter(VerificationHistory.status == "INVALID").count()
        risky = db.query(VerificationHistory).filter(VerificationHistory.status == "RISKY").count()
        unknown = db.query(VerificationHistory).filter(VerificationHistory.status == "UNKNOWN").count()
        
        avg_score_res = db.query(func.avg(VerificationHistory.score)).scalar()
        avg_score = round(float(avg_score_res), 1) if avg_score_res is not None else 0.0
        valid_rate = round((valid / total) * 100, 1) if total > 0 else 0.0

        recent_items = db.query(VerificationHistory).order_by(desc(VerificationHistory.created_at)).limit(10).all()
        recent_activity = [
            {
                "id": item.id,
                "email": item.email,
                "domain": item.domain,
                "status": item.status,
                "score": item.score,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in recent_items
        ]

        return StatsSummary(
            total_verified=total,
            valid_count=valid,
            invalid_count=invalid,
            risky_count=risky,
            unknown_count=unknown,
            valid_rate=valid_rate,
            average_score=avg_score,
            recent_activity=recent_activity,
        )

history_service = HistoryService()

import io
import csv
import time
import logging
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.verification import (
    VerifyRequest,
    BatchVerifyRequest,
    VerifyResponse,
    BatchVerifyResponse,
    HistoryListResponse,
    HistoryItem,
    StatsSummary,
)
from app.services.verification_service import verification_service
from app.services.history_service import history_service
from app.services.document_extractor import document_extractor
from app.core.config import settings

logger = logging.getLogger("mailscope.endpoints")
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
    history_service.record_verification(db, result)
    return result

def _verify_single_safe(cleaned: str) -> VerifyResponse:
    try:
        return verification_service.verify_email(cleaned)
    except Exception as exc:
        res = verification_service.verify_email("invalid@unknown-error.local")
        res.email = cleaned
        res.normalized_email = cleaned.lower()
        res.status = "UNKNOWN"
        res.final_status = "UNKNOWN"
        res.classification = "UNKNOWN"
        res.message = f"Verification error: {str(exc)[:100]}"
        res.reason = "Unexpected error during verification."
        return res

@router.post("/verify/batch", response_model=BatchVerifyResponse, summary="Batch verify up to 100 email addresses")
def batch_verify_emails(
    payload: BatchVerifyRequest,
    db: Session = Depends(get_db)
):
    raw_emails = payload.emails
    if not raw_emails:
        raise HTTPException(status_code=400, detail="Email list cannot be empty.")
    
    if len(raw_emails) > settings.MAX_BULK_EMAILS:
        raise HTTPException(
            status_code=400,
            detail=f"Too many email addresses. Maximum allowed: {settings.MAX_BULK_EMAILS}."
        )
    
    cleaned_list = [e.strip() for e in raw_emails if e and e.strip()]
    if not cleaned_list:
        raise HTTPException(status_code=400, detail="No valid email strings provided.")

    t_batch_start = time.perf_counter()

    # Controlled concurrency worker pool for rate-limited batch verification
    max_workers = min(settings.BULK_CONCURRENCY, len(cleaned_list))
    if max_workers < 1:
        max_workers = 1

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results_list = list(executor.map(_verify_single_safe, cleaned_list))

    t_batch_end = time.perf_counter()
    total_batch_time_ms = round((t_batch_end - t_batch_start) * 1000, 2)

    results: List[VerifyResponse] = []
    valid_c = 0
    invalid_c = 0
    risky_c = 0
    unknown_c = 0
    total_score = 0

    for res in results_list:
        results.append(res)
        history_service.record_verification(db, res)
        
        if res.status == "VALID" or res.classification == "REAL":
            valid_c += 1
        elif res.status == "INVALID" or res.classification == "INVALID":
            invalid_c += 1
        elif res.status == "RISKY" or res.classification == "RISKY":
            risky_c += 1
        else:
            unknown_c += 1
            
        total_score += res.score

    total = len(results)
    avg_score = round(total_score / total, 1) if total > 0 else 0.0
    avg_verify_time = round(total_batch_time_ms / total, 2) if total > 0 else 0.0
    emails_per_sec = round(total / (total_batch_time_ms / 1000), 2) if total_batch_time_ms > 0 else 0.0

    return BatchVerifyResponse(
        total=total,
        valid_count=valid_c,
        invalid_count=invalid_c,
        risky_count=risky_c,
        unknown_count=unknown_c,
        average_score=avg_score,
        total_batch_time_ms=total_batch_time_ms,
        average_verification_time_ms=avg_verify_time,
        emails_per_second=emails_per_sec,
        results=results,
    )

@router.post("/extract-document", summary="Extract email addresses from PDF or Word document")
async def extract_emails_from_document(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided.")
    
    filename = file.filename or "uploaded_document"
    ext = filename.lower().split(".")[-1]
    if ext not in ["pdf", "docx", "doc"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '.{ext}'. Supported formats: .pdf, .docx, .doc")
    
    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB.")

    try:
        extraction_res = document_extractor.process_document(filename, content)
        return extraction_res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in extract-document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@router.post("/export/batch", summary="Export batch verification results to CSV, XLSX, or PDF")
def export_batch_results(
    format: str = Query("csv", description="Export format: csv, xlsx, or pdf"),
    results: List[Dict[str, Any]] = Body(...)
):
    if not results:
        raise HTTPException(status_code=400, detail="No verification results provided to export.")

    headers = [
        "Email", "Domain", "Syntax", "DNS", "MX", "SMTP Status", 
        "SMTP Response", "Catch-all", "Disposable", "Role Account", 
        "Classification", "Reason", "Verification Time", "Timestamp"
    ]

    rows = []
    for item in results:
        checks = item.get("checks", {})
        syn = checks.get("syntax", {}).get("display_value", "PASS" if item.get("syntax_valid") else "FAIL")
        dns = checks.get("dns", {}).get("display_value", "PASS" if item.get("dns_resolved") else "FAIL")
        mx = checks.get("mx", {}).get("display_value", "FOUND" if item.get("mx_found") else "NOT FOUND")
        smtp_st = checks.get("smtp", {}).get("display_value", item.get("smtp_connection_status", "UNKNOWN"))
        rcpt_resp = item.get("smtp_recipient_response") or item.get("reason") or "N/A"
        catch_all = "YES" if item.get("catch_all_detected") else "NO"
        disposable = "YES" if item.get("disposable_detected") else "NO"
        role_acc = "YES" if item.get("role_account_detected") else "NO"
        classification = item.get("final_status") or item.get("classification") or item.get("status") or "UNKNOWN"
        reason = item.get("reason") or item.get("message") or "N/A"
        timestamp = item.get("verified_at") or "N/A"

        rows.append([
            item.get("email", ""),
            item.get("domain", ""),
            syn,
            dns,
            mx,
            smtp_st,
            rcpt_resp,
            catch_all,
            disposable,
            role_acc,
            classification,
            reason,
            "Non-Contact Technical SMTP Probe",
            timestamp
        ])

    fmt = format.lower()
    if fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=mailscope_batch_audit.csv"}
        )

    elif fmt == "xlsx":
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "MailScope Batch Audit"
        ws.append(headers)
        for row in rows:
            ws.append(row)
        out_bytes = io.BytesIO()
        wb.save(out_bytes)
        out_bytes.seek(0)
        return StreamingResponse(
            out_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=mailscope_batch_audit.xlsx"}
        )

    elif fmt == "pdf":
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        out_bytes = io.BytesIO()
        doc = SimpleDocTemplate(out_bytes, pagesize=landscape(letter), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle("TitleStyle", parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor("#0f172a"))
        elements.append(Paragraph("MailScope - Batch Email Verification Audit Report", title_style))
        elements.append(Spacer(1, 10))

        pdf_table_data = [["Email", "Domain", "Syntax", "MX", "SMTP", "Classification", "Reason"]]
        for r in rows:
            pdf_table_data.append([
                r[0][:25],
                r[1][:18],
                r[2],
                r[4],
                r[5],
                r[10],
                r[11][:35]
            ])

        t = Table(pdf_table_data, colWidths=[130, 100, 45, 65, 70, 110, 220])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 8),
        ]))
        elements.append(t)
        doc.build(elements)
        out_bytes.seek(0)
        return StreamingResponse(
            out_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=mailscope_batch_audit.pdf"}
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format '{format}'. Supported: csv, xlsx, pdf")

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

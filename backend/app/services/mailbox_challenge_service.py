import secrets
import hashlib
import hmac
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from threading import Lock
import logging
from app.core.config import settings

logger = logging.getLogger("mailscope.delivery")

class MailboxChallengeService:
    def __init__(self):
        self._challenges: Dict[str, Dict[str, Any]] = {}
        self._verified_mailboxes: Dict[str, float] = {} # email -> verified_timestamp
        self._lock = Lock()

    def _hash_code(self, salt: str, code: str) -> str:
        """Computes salted SHA-256 hash of the verification code."""
        return hashlib.sha256(f"{salt}:{code}".encode("utf-8")).hexdigest()

    def generate_and_send_code(self, email: str) -> Dict[str, Any]:
        """
        Generates a secure 6-digit one-time verification code, stores ONLY its salted SHA-256 hash,
        enforces cooldown & rate-limits, and sends the code via REAL SMTP service.
        Only returns success=True if the SMTP message is successfully accepted by the mail server.
        """
        normalized = (email or "").strip().lower()
        if not normalized or "@" not in normalized:
            return {
                "success": False,
                "error": "Invalid email address format.",
                "status_code": 400
            }

        # Check SMTP configuration before proceeding
        if not settings.SMTP_HOST:
            logger.warning("SMTP_HOST is not configured in backend environment (.env). Cannot send real email.")
            return {
                "success": False,
                "error": "Outbound SMTP server is not configured. Please set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, and SMTP_PASSWORD in backend/.env to send real emails.",
                "status_code": 503
            }

        with self._lock:
            now = time.time()
            existing = self._challenges.get(normalized)
            
            # Enforce resend cooldown (60 seconds)
            if existing:
                elapsed = now - existing.get("last_sent_at", 0)
                cooldown = settings.OTP_RESEND_COOLDOWN_SECONDS
                if elapsed < cooldown:
                    remaining_wait = int(cooldown - elapsed)
                    return {
                        "success": False,
                        "error": f"Please wait {remaining_wait}s before requesting a new verification code.",
                        "cooldown_remaining": remaining_wait,
                        "status_code": 429
                    }

            # Generate 6-digit cryptographically secure random code
            code = f"{secrets.randbelow(900000) + 100000}"
            salt = secrets.token_hex(16)
            code_hash = self._hash_code(salt, code)
            expires_at = now + settings.OTP_EXPIRATION_SECONDS

            # Save challenge record
            self._challenges[normalized] = {
                "salt": salt,
                "code_hash": code_hash,
                "created_at": now,
                "last_sent_at": now,
                "expires_at": expires_at,
                "attempts_remaining": settings.OTP_MAX_ATTEMPTS,
            }

        # Dispatch real email via SMTP
        send_res = self._dispatch_email(normalized, code)
        
        if not send_res.get("success"):
            # If email delivery failed, remove challenge so user can retry after fixing credentials
            with self._lock:
                if normalized in self._challenges:
                    del self._challenges[normalized]
            
            return {
                "success": False,
                "error": send_res.get("error", "Unable to send verification email. Please try again."),
                "status_code": 500
            }

        return {
            "success": True,
            "message": f"Verification code sent to {normalized}",
            "expires_in_seconds": settings.OTP_EXPIRATION_SECONDS,
            "cooldown_seconds": settings.OTP_RESEND_COOLDOWN_SECONDS,
            "delivery_mode": "live_smtp",
            "status_code": 200
        }

    def verify_code(self, email: str, submitted_code: str) -> Dict[str, Any]:
        """
        Validates the submitted 6-digit code against the stored salted hash.
        Enforces expiration and max-attempts limits.
        """
        normalized = (email or "").strip().lower()
        cleaned_code = (submitted_code or "").strip()

        if not normalized or not cleaned_code:
            return {
                "success": False,
                "error": "Email and verification code are required.",
                "status_code": 400
            }

        with self._lock:
            now = time.time()
            challenge = self._challenges.get(normalized)

            if not challenge:
                return {
                    "success": False,
                    "error": "No active verification code found. Please request a new code.",
                    "status_code": 404
                }

            # Check expiration
            if now > challenge["expires_at"]:
                del self._challenges[normalized]
                return {
                    "success": False,
                    "error": "Verification code has expired. Please request a new code.",
                    "status_code": 400
                }

            # Check attempts remaining
            if challenge["attempts_remaining"] <= 0:
                del self._challenges[normalized]
                return {
                    "success": False,
                    "error": "Maximum verification attempts exceeded. Please request a new code.",
                    "status_code": 429
                }

            # Verify hash using constant-time comparison
            expected_hash = challenge["code_hash"]
            computed_hash = self._hash_code(challenge["salt"], cleaned_code)

            if hmac.compare_digest(expected_hash, computed_hash):
                # SUCCESS: Mark mailbox as verified
                self._verified_mailboxes[normalized] = now
                del self._challenges[normalized] # Invalidate challenge after successful use
                return {
                    "success": True,
                    "message": "Mailbox ownership verified successfully.",
                    "verified_at": now,
                    "status_code": 200
                }
            else:
                challenge["attempts_remaining"] -= 1
                rem = challenge["attempts_remaining"]
                if rem <= 0:
                    del self._challenges[normalized]
                    return {
                        "success": False,
                        "error": "Invalid verification code. Maximum attempts exceeded. Please request a new code.",
                        "attempts_remaining": 0,
                        "status_code": 400
                    }
                return {
                    "success": False,
                    "error": f"Invalid verification code. {rem} attempt{'s' if rem != 1 else ''} remaining.",
                    "attempts_remaining": rem,
                    "status_code": 400
                }

    def is_mailbox_verified(self, email: str) -> bool:
        """Checks if the email address mailbox has completed code verification in the active session."""
        normalized = (email or "").strip().lower()
        with self._lock:
            return normalized in self._verified_mailboxes

    def _dispatch_email(self, target_email: str, code: str) -> Dict[str, Any]:
        """
        Sends the verification code email via SMTP.
        Only returns success=True when SMTP server successfully accepts recipient message.
        """
        smtp_host = settings.SMTP_HOST
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USERNAME
        smtp_pass = settings.SMTP_PASSWORD
        from_email = settings.SMTP_FROM_EMAIL

        if not smtp_host:
            return {
                "success": False,
                "error": "SMTP server host is not configured. Please set SMTP_HOST in .env"
            }

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Verify your email address - MailScope"
            msg["From"] = f"MailScope <{from_email}>"
            msg["To"] = target_email

            text_content = f"""MailScope
Email Verification

Your verification code is:

{code}

This code expires in 10 minutes.

If you did not request this verification, you can ignore this email.

— MailScope Verification Engine
"""
            html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #0f172a; padding: 24px; margin: 0; }}
    .container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 36px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    .header {{ font-size: 22px; font-weight: 800; color: #0f2744; margin-bottom: 6px; letter-spacing: -0.5px; }}
    .sub {{ font-size: 14px; color: #64748b; margin-bottom: 24px; }}
    .code-card {{ background: #f0f7ff; border: 1.5px dashed #0284c7; border-radius: 10px; padding: 20px; text-align: center; margin: 24px 0; }}
    .code-label {{ font-size: 11px; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; color: #0369a1; margin-bottom: 8px; }}
    .code-val {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #0284c7; }}
    .note {{ font-size: 13px; color: #475569; line-height: 1.5; margin: 16px 0; }}
    .footer {{ font-size: 11px; color: #94a3b8; border-top: 1px solid #f1f5f9; padding-top: 20px; margin-top: 28px; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">MailScope</div>
    <div class="sub">Email Mailbox Ownership Verification</div>
    <p class="note">Please use the verification code below to confirm access and ownership of your mailbox:</p>
    <div class="code-card">
      <div class="code-label">One-Time Verification Code</div>
      <div class="code-val">{code}</div>
    </div>
    <p class="note">This code expires in <strong>10 minutes</strong>. Do not share this code with anyone.</p>
    <p class="note" style="color: #64748b; font-size: 12px;">If you did not request this verification, you can safely ignore this email.</p>
    <div class="footer">&copy; MailScope &bull; Open-Source Email Validation & Intelligence Engine</div>
  </div>
</body>
</html>"""

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Connect via SSL or TLS
            if settings.SMTP_USE_SSL or smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=12.0)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=12.0)
                if settings.SMTP_USE_TLS:
                    server.starttls()

            with server:
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.sendmail(from_email, [target_email], msg.as_string())

            logger.info(f"Verification code email successfully sent to {target_email} via SMTP {smtp_host}:{smtp_port}")
            return {"success": True, "mode": "live_smtp"}

        except smtplib.SMTPAuthenticationError as e:
            err = f"SMTP Authentication failed. Please verify SMTP_USERNAME and SMTP_PASSWORD in backend/.env: {str(e)}"
            logger.error(err)
            return {"success": False, "error": "SMTP authentication failed. Please check backend mail credentials."}

        except (smtplib.SMTPConnectError, ConnectionRefusedError, TimeoutError, smtplib.SMTPTimeoutError) as e:
            err = f"SMTP Connection failed to {smtp_host}:{smtp_port}: {str(e)}"
            logger.error(err)
            return {"success": False, "error": f"Could not connect to outbound mail server ({smtp_host}:{smtp_port})."}

        except smtplib.SMTPRecipientsRefused as e:
            err = f"SMTP recipient refused for {target_email}: {str(e)}"
            logger.error(err)
            return {"success": False, "error": f"Mail server refused recipient address ({target_email})."}

        except Exception as e:
            err = f"SMTP send error to {target_email}: {str(e)}"
            logger.error(err)
            return {"success": False, "error": "Unable to send verification email. Please check SMTP settings and try again."}

mailbox_challenge_service = MailboxChallengeService()

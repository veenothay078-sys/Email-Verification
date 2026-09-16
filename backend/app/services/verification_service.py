import re
import socket
import smtplib
import uuid
import logging
from typing import Dict, Any, Tuple, List, Optional
from email_validator import validate_email, EmailNotValidError
from app.services.dns_service import dns_service
from app.services.smtp_service import smtp_service
from app.services.mailbox_challenge_service import mailbox_challenge_service
from app.data.disposable_domains import is_disposable_domain
from app.data.role_prefixes import is_role_based_local_part, is_free_email_domain
from app.schemas.verification import (
    VerifyResponse,
    VerificationChecks,
    CheckDetail,
    DomainIntelligence,
)

logger = logging.getLogger("mailscope.verification")

class VerificationEngine:
    """
    Modular Multi-Signal Email Validation and Deliverability Verification Engine.
    Executes a 12-stage technical inspection pipeline:
    EMAIL ➔ SYNTAX ➔ DOMAIN ➔ DNS ➔ MX ➔ SMTP CONNECT ➔ RECIPIENT PROBE ➔ CATCH-ALL ➔ DISPOSABLE ➔ ROLE-BASED ➔ FREE-MAIL ➔ CONFIDENCE & CLASSIFICATION
    """

    def validateSyntax(self, raw_email: str) -> Dict[str, Any]:
        """
        Stage 1: Validates RFC 5322 syntax, local-part format, @ separator, and domain structure.
        """
        cleaned = (raw_email or "").strip()
        if not cleaned:
            return {
                "passed": False,
                "display_value": "FAIL",
                "normalized_email": "",
                "local_part": "",
                "domain": "",
                "message": "Email address cannot be empty.",
            }

        # Check for basic illegal formatting
        if cleaned.count("@") != 1 or ".." in cleaned or cleaned.startswith(".") or cleaned.endswith("."):
            parts = cleaned.split("@")
            return {
                "passed": False,
                "display_value": "FAIL",
                "normalized_email": cleaned.lower(),
                "local_part": parts[0] if len(parts) > 0 else "",
                "domain": parts[1].lower() if len(parts) > 1 else "",
                "message": "Malformed email format or invalid character placement.",
            }

        try:
            valid_info = validate_email(cleaned, check_deliverability=False)
            return {
                "passed": True,
                "display_value": "PASS",
                "normalized_email": valid_info.normalized,
                "local_part": valid_info.local_part,
                "domain": valid_info.domain.lower(),
                "message": "Email conforms to RFC 5322 syntax standards.",
            }
        except EmailNotValidError as e:
            parts = cleaned.split("@")
            return {
                "passed": False,
                "display_value": "FAIL",
                "normalized_email": cleaned.lower(),
                "local_part": parts[0] if len(parts) > 0 else "",
                "domain": parts[1].lower() if len(parts) > 1 else "",
                "message": f"Invalid syntax: {str(e)}",
            }

    def checkDomain(self, domain: str) -> Dict[str, Any]:
        """
        Stage 2: Checks domain format and basic structure.
        """
        if not domain or "." not in domain or domain.startswith(".") or domain.endswith(".") or domain.startswith("-") or domain.endswith("-"):
            return {
                "passed": False,
                "display_value": "FAIL",
                "message": f"Domain '{domain}' has an invalid format.",
            }
        
        # Check domain label lengths
        labels = domain.split(".")
        for label in labels:
            if not label or len(label) > 63:
                return {
                    "passed": False,
                    "display_value": "FAIL",
                    "message": f"Invalid domain label in '{domain}'.",
                }

        return {
            "passed": True,
            "display_value": "PASS",
            "message": f"Domain '{domain}' format is valid.",
        }

    def checkDNS(self, domain: str) -> Dict[str, Any]:
        """
        Stage 3: Performs real DNS resolution (A/AAAA records) with timeout handling.
        """
        if not domain:
            return {
                "passed": False,
                "display_value": "FAIL",
                "is_timeout": False,
                "a_records": [],
                "message": "DNS resolution skipped (missing domain).",
            }

        dns_res = dns_service.check_domain_dns(domain)

        if dns_res.get("is_timeout"):
            return {
                "passed": False,
                "display_value": "UNKNOWN",
                "is_timeout": True,
                "a_records": [],
                "raw": dns_res,
                "message": "DNS query timed out (nameserver delay).",
            }

        if not dns_res.get("is_resolvable"):
            return {
                "passed": False,
                "display_value": "FAIL",
                "is_timeout": False,
                "a_records": [],
                "raw": dns_res,
                "message": dns_res.get("error") or "Domain does not resolve to active DNS records.",
            }

        ip_count = len(dns_res.get("a_records", []))
        return {
            "passed": True,
            "display_value": "PASS",
            "is_timeout": False,
            "a_records": dns_res.get("a_records", []),
            "raw": dns_res,
            "message": f"Domain resolved successfully ({ip_count} active IP record{'s' if ip_count != 1 else ''}).",
        }

    def checkMX(self, domain: str, dns_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 4: Inspects Mail Exchange (MX) records, priority ordering, and routing hosts.
        Enforces invariant: MX exists ≠ Mailbox exists.
        """
        raw_dns = dns_result.get("raw", {})
        if dns_result.get("is_timeout"):
            return {
                "passed": False,
                "display_value": "UNKNOWN",
                "is_timeout": True,
                "mx_records": [],
                "message": "MX check inconclusive due to DNS timeout.",
            }

        if not raw_dns.get("has_mx") or not raw_dns.get("mx_records"):
            return {
                "passed": False,
                "display_value": "FAIL",
                "is_timeout": False,
                "mx_records": [],
                "message": "No mail exchange (MX) servers configured for this domain.",
            }

        mx_records = raw_dns.get("mx_records", [])
        primary = mx_records[0].get("host", "") if mx_records else ""
        return {
            "passed": True,
            "display_value": "PASS",
            "is_timeout": False,
            "mx_records": mx_records,
            "primary_host": primary,
            "message": f"{len(mx_records)} MX record{'s' if len(mx_records) != 1 else ''} configured (Primary: {primary}).",
        }

    def checkSMTP(self, email: str, domain: str, mx_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Stages 5, 6, 7: Server-side SMTP connectivity, Recipient-level RCPT TO probing, and Catch-All detection.
        Uses 2.0s safe socket timeout. Does NOT send actual email messages.
        """
        if not email or not domain or not mx_records:
            return {
                "attempted": False,
                "connected": False,
                "smtp_status": "SKIPPED",
                "mailbox_status": "UNCONFIRMED",
                "is_catch_all": False,
                "server_code": None,
                "server_message": "SMTP probe skipped (no usable MX servers).",
                "mx_host_used": None,
                "details": {},
            }

        return smtp_service.verify_mailbox_smtp(
            email=email,
            domain=domain,
            mx_records=mx_records
        )

    def detectDisposable(self, domain: str) -> Dict[str, Any]:
        """
        Stage 8: Detects known temporary / disposable inbox providers.
        """
        is_disp = is_disposable_domain(domain)
        return {
            "is_disposable": is_disp,
            "display_value": "YES" if is_disp else "NO",
            "passed": not is_disp,
            "message": "Domain matches a known disposable email provider." if is_disp else "Domain is not identified as a disposable inbox.",
        }

    def detectRoleBased(self, local_part: str) -> Dict[str, Any]:
        """
        Stage 9: Detects generic role-based prefixes (e.g. info, support, admin, sales).
        """
        is_role = is_role_based_local_part(local_part)
        return {
            "is_role_based": is_role,
            "display_value": "YES" if is_role else "NO",
            "passed": not is_role,
            "message": "Address is role-based (team/department alias)." if is_role else "Address is individual, not a generic role alias.",
        }

    def detectFreeMail(self, domain: str) -> Dict[str, Any]:
        """
        Stage 10: Identifies consumer free-mail providers (Gmail, Outlook, Yahoo, etc.).
        Informational only - NOT penalized in scoring.
        """
        is_free = is_free_email_domain(domain)
        return {
            "is_free_provider": is_free,
            "display_value": "YES" if is_free else "NO",
            "passed": True,
            "message": f"Domain is hosted by consumer provider ({domain})." if is_free else "Domain is a custom/corporate business domain.",
        }

    def calculateConfidence(self, signals: Dict[str, Any]) -> int:
        """
        Stage 11: Multi-Signal Deterministic Confidence Calculation Engine.
        Calculates verification score based strictly on technical evidence (0 to 100).
        """
        # Hard fatal failure checks -> 0
        if not signals["syntax"]["passed"] or not signals["domain"]["passed"]:
            return 0
        if not signals["dns"]["passed"] and not signals["dns"].get("is_timeout"):
            return 0
        if not signals["mx"]["passed"] and not signals["mx"].get("is_timeout"):
            return 0
        if signals["smtp"]["smtp_status"] == "REJECTED" or signals["smtp"]["mailbox_status"] in ["NOT_FOUND", "REJECTED"]:
            return 0

        # Mailbox Verified via One-Time Confirmation Code -> 100
        if signals.get("is_otp_verified"):
            return 100

        # Mailbox Positively Confirmed by Destination Mail Server (250 OK) -> 100
        if signals["smtp"]["smtp_status"] == "ACCEPTED" and signals["smtp"]["mailbox_status"] == "CONFIRMED":
            return 100

        # Deterministic weighted signal aggregation
        score = 0

        # 1. Syntax Pass (+20)
        if signals["syntax"]["passed"]:
            score += 20

        # 2. Domain Format Pass (+15)
        if signals["domain"]["passed"]:
            score += 15

        # 3. DNS Resolution Pass (+15)
        if signals["dns"]["passed"]:
            score += 15
        elif signals["dns"].get("is_timeout"):
            score += 5

        # 4. MX Record Configuration Pass (+20)
        if signals["mx"]["passed"]:
            score += 20
        elif signals["mx"].get("is_timeout"):
            score += 5

        # 5. SMTP Server Connectivity (+10)
        if signals["smtp"]["connected"]:
            score += 10
        elif signals["smtp"]["smtp_status"] in ["BLOCKED", "TIMEOUT", "GREYLISTED"]:
            score += 5 # Infrastructure exists, network filtered

        # 6. Risk Penalties
        if signals["disposable"]["is_disposable"]:
            score -= 20
        if signals["role_based"]["is_role_based"]:
            score -= 10
        if signals["smtp"].get("is_catch_all"):
            score -= 10

        # Clamp strictly between 0 and 100
        return max(0, min(100, score))

    def classifyResult(self, signals: Dict[str, Any], confidence: int) -> Tuple[str, str, str]:
        """
        Stage 12: Final Result Classification Engine.
        Classifies strictly into VALID, INVALID, RISKY, or UNKNOWN with comprehensive rationale.
        """
        # --- 1. INVALID: Clear Negative Evidence ---
        if not signals["syntax"]["passed"]:
            return (
                "INVALID",
                "Email address syntax is invalid.",
                signals["syntax"]["message"]
            )

        if not signals["domain"]["passed"]:
            return (
                "INVALID",
                "Email address has an invalid domain format.",
                signals["domain"]["message"]
            )

        if not signals["dns"]["passed"]:
            if signals["dns"].get("is_timeout"):
                return (
                    "UNKNOWN",
                    "DNS lookup timed out. Nameserver delay prevents conclusive verification.",
                    "Temporary DNS query timeout. Verification is inconclusive."
                )
            return (
                "INVALID",
                "Domain does not exist or does not resolve to active DNS records.",
                signals["dns"]["message"]
            )

        if not signals["mx"]["passed"]:
            if signals["mx"].get("is_timeout"):
                return (
                    "UNKNOWN",
                    "MX lookup timed out. Mail routing could not be verified.",
                    "Temporary MX query timeout. Verification is inconclusive."
                )
            return (
                "INVALID",
                "No usable mail exchange (MX) servers configured for this domain.",
                signals["mx"]["message"]
            )

        if signals["smtp"]["smtp_status"] == "REJECTED" or signals["smtp"]["mailbox_status"] in ["NOT_FOUND", "REJECTED"]:
            return (
                "INVALID",
                "Destination mail server rejected the recipient mailbox (User unknown / 550).",
                signals["smtp"]["server_message"] or "Mailbox does not exist on destination server."
            )

        # --- 2. RISKY: Risk Signals Detected ---
        if signals["disposable"]["is_disposable"]:
            return (
                "RISKY",
                "Domain matches a known disposable temporary email provider.",
                "Email address appears technically functional but is hosted by a disposable inbox provider."
            )

        if signals["role_based"]["is_role_based"]:
            return (
                "RISKY",
                "Address appears to be role-based (department/group alias).",
                "Email address is a role-based mailbox (e.g. support, admin, info), which carries higher bounce/unattended risks."
            )

        if signals["smtp"].get("is_catch_all"):
            return (
                "RISKY",
                "Destination domain operates a Catch-All policy, accepting arbitrary recipient prefixes.",
                "Domain accepts all incoming mailboxes, making specific recipient verification inconclusive."
            )

        # --- 3. VALID: Strong Positive Technical Evidence ---
        if signals.get("is_otp_verified"):
            return (
                "VALID",
                "Mailbox ownership and accessibility verified via one-time confirmation code.",
                "✓ Mailbox verified. Verification code confirmed."
            )

        if signals["smtp"]["smtp_status"] == "ACCEPTED" and signals["smtp"]["mailbox_status"] == "CONFIRMED":
            return (
                "VALID",
                "Mailbox existence confirmed by destination mail server (250 OK).",
                "Email passed all technical, domain, and server recipient mailbox verification checks."
            )

        # --- 4. UNKNOWN: Insufficient / Blocked / Indeterminate Evidence ---
        # When domain/MX are active, but SMTP handshake was restricted by ISP/firewall and OTP is unverified
        return (
            "UNKNOWN",
            "Mailbox existence unconfirmed (SMTP restricted). Mailbox verification required to confirm access.",
            "Domain and mail server infrastructure are active. Send a verification code to confirm mailbox access."
        )

    def verify_email(self, email: str) -> VerifyResponse:
        """
        Executes the complete multi-signal verification pipeline and returns standard VerifyResponse.
        """
        raw_email = (email or "").strip()

        # 1. Syntax Validation
        syntax_res = self.validateSyntax(raw_email)
        normalized_email = syntax_res["normalized_email"]
        local_part = syntax_res["local_part"]
        domain = syntax_res["domain"]

        # 2. Domain Format Analysis
        domain_res = self.checkDomain(domain) if syntax_res["passed"] else {
            "passed": False,
            "display_value": "FAIL",
            "message": "Domain check skipped due to syntax error.",
        }

        # 3. DNS Resolution
        dns_res = self.checkDNS(domain) if domain_res["passed"] else {
            "passed": False,
            "display_value": "FAIL",
            "is_timeout": False,
            "a_records": [],
            "message": "DNS check skipped (invalid domain).",
        }

        # 4. MX Records Analysis
        mx_res = self.checkMX(domain, dns_res) if dns_res["passed"] else {
            "passed": False,
            "display_value": "FAIL",
            "is_timeout": dns_res.get("is_timeout", False),
            "mx_records": [],
            "message": "MX check skipped (domain unresolvable).",
        }

        # 5. Disposable Detection
        disp_res = self.detectDisposable(domain) if domain else {
            "is_disposable": False,
            "display_value": "NO",
            "passed": True,
            "message": "Disposable check skipped.",
        }

        # 6. Role-Based Detection
        role_res = self.detectRoleBased(local_part) if local_part else {
            "is_role_based": False,
            "display_value": "NO",
            "passed": True,
            "message": "Role-based check skipped.",
        }

        # 7. Free-Mail Detection
        free_res = self.detectFreeMail(domain) if domain else {
            "is_free_provider": False,
            "display_value": "NO",
            "passed": True,
            "message": "Free-mail check skipped.",
        }

        # 8. Server-Side SMTP Probing
        smtp_res = self.checkSMTP(
            email=normalized_email,
            domain=domain,
            mx_records=mx_res.get("mx_records", [])
        ) if mx_res["passed"] else {
            "attempted": False,
            "connected": False,
            "smtp_status": "SKIPPED",
            "mailbox_status": "UNCONFIRMED",
            "is_catch_all": False,
            "server_code": None,
            "server_message": "SMTP probe skipped.",
            "mx_host_used": None,
            "details": {},
        }

        # 9. Mailbox OTP Verified State
        is_otp_verified = mailbox_challenge_service.is_mailbox_verified(normalized_email)
        if is_otp_verified:
            smtp_res["mailbox_status"] = "CONFIRMED"

        # Signal Aggregation
        signals = {
            "syntax": syntax_res,
            "domain": domain_res,
            "dns": dns_res,
            "mx": mx_res,
            "smtp": smtp_res,
            "disposable": disp_res,
            "role_based": role_res,
            "free_mail": free_res,
            "is_otp_verified": is_otp_verified,
        }

        # 10. Multi-Signal Deterministic Confidence Calculation
        confidence = self.calculateConfidence(signals)

        # 11. Final Classification
        status, reason, message = self.classifyResult(signals, confidence)

        # Normalize display values for UI
        smtp_display_map = {
            "ACCEPTED": "ACCEPTED",
            "REJECTED": "REJECTED",
            "BLOCKED": "BLOCKED",
            "TIMEOUT": "TIMEOUT",
            "GREYLISTED": "BLOCKED",
            "SKIPPED": "UNKNOWN",
            "UNKNOWN": "UNKNOWN"
        }
        smtp_display_val = smtp_display_map.get(smtp_res.get("smtp_status"), "UNKNOWN")

        mailbox_display_map = {
            "CONFIRMED": "CONFIRMED",
            "NOT_FOUND": "REJECTED",
            "REJECTED": "REJECTED",
            "CATCH_ALL": "UNCONFIRMED",
            "UNCONFIRMED": "UNCONFIRMED"
        }
        mailbox_display_val = "CONFIRMED" if is_otp_verified else mailbox_display_map.get(smtp_res.get("mailbox_status"), "UNCONFIRMED")

        checks = VerificationChecks(
            syntax=CheckDetail(
                passed=syntax_res["passed"],
                status=syntax_res["display_value"],
                display_value=syntax_res["display_value"],
                message=syntax_res["message"],
                details={"local_part": local_part, "domain": domain}
            ),
            domain=CheckDetail(
                passed=domain_res["passed"],
                status=domain_res["display_value"],
                display_value=domain_res["display_value"],
                message=domain_res["message"],
                details={"domain": domain}
            ),
            dns=CheckDetail(
                passed=dns_res["passed"],
                status=dns_res["display_value"],
                display_value=dns_res["display_value"],
                message=dns_res["message"],
                details={"a_records": dns_res.get("a_records", [])}
            ),
            mx=CheckDetail(
                passed=mx_res["passed"],
                status=mx_res["display_value"],
                display_value=mx_res["display_value"],
                message=mx_res["message"],
                details={"mx_records": mx_res.get("mx_records", [])}
            ),
            smtp=CheckDetail(
                passed=smtp_res.get("smtp_status") == "ACCEPTED" or smtp_res.get("connected", False),
                status=smtp_display_val,
                display_value=smtp_display_val,
                message=smtp_res.get("server_message") or ("Mail server reachable." if smtp_res.get("connected") else "SMTP probe restricted."),
                details=smtp_res
            ),
            mailbox=CheckDetail(
                passed=mailbox_display_val == "CONFIRMED",
                status=mailbox_display_val,
                display_value=mailbox_display_val,
                message="✓ Mailbox verified. Verification code confirmed." if is_otp_verified else (
                    "Mailbox existence confirmed by destination mail server (250 OK)." if smtp_res.get("mailbox_status") == "CONFIRMED" else (
                        "Mailbox rejected by destination mail server." if smtp_res.get("mailbox_status") in ["NOT_FOUND", "REJECTED"] else
                        "Mailbox unconfirmed. Send a verification code to confirm access." if status == "UNKNOWN" else
                        f"Mailbox status: {mailbox_display_val}"
                    )
                ),
                details={"status": mailbox_display_val, "is_catch_all": smtp_res.get("is_catch_all", False), "is_otp_verified": is_otp_verified}
            ),
            disposable=CheckDetail(
                passed=disp_res["passed"],
                status=disp_res["display_value"],
                display_value=disp_res["display_value"],
                message=disp_res["message"],
                details={"is_disposable": disp_res["is_disposable"]}
            ),
            role_based=CheckDetail(
                passed=role_res["passed"],
                status=role_res["display_value"],
                display_value=role_res["display_value"],
                message=role_res["message"],
                details={"is_role_based": role_res["is_role_based"], "local_part": local_part}
            ),
            free_provider=CheckDetail(
                passed=True,
                status=free_res["display_value"],
                display_value=free_res["display_value"],
                message=free_res["message"],
                details={"is_free_provider": free_res["is_free_provider"]}
            ),
            catch_all=CheckDetail(
                passed=not smtp_res.get("is_catch_all", False),
                status="YES" if smtp_res.get("is_catch_all") else "NO",
                display_value="YES" if smtp_res.get("is_catch_all") else "NO",
                message="Domain operates Catch-All mail routing." if smtp_res.get("is_catch_all") else "Domain uses standard mailbox routing.",
                details={"is_catch_all": smtp_res.get("is_catch_all", False)}
            )
        )

        domain_intel = DomainIntelligence(
            domain=domain or "unknown",
            is_resolvable=dns_res["passed"],
            mx_records=mx_res.get("mx_records", []),
            a_records=dns_res.get("a_records", []),
            is_disposable=disp_res["is_disposable"],
            is_free_provider=free_res["is_free_provider"],
            is_catch_all=smtp_res.get("is_catch_all", False),
            has_mail_server=mx_res["passed"],
            smtp_verified=smtp_res.get("connected", False),
            smtp_status=smtp_display_val,
            mailbox_status=mailbox_display_val,
        )

        return VerifyResponse(
            email=raw_email,
            normalized_email=normalized_email,
            domain=domain,
            status=status,
            score=confidence,
            confidence=confidence,
            checks=checks,
            domain_intelligence=domain_intel,
            message=message,
            reason=reason,
        )

verification_service = VerificationEngine()

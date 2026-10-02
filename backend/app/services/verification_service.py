import re
import time
import socket
import logging
from typing import Dict, Any, Tuple, List, Optional
from email_validator import validate_email, EmailNotValidError
from app.services.dns_service import dns_service
from app.services.smtp_service import smtp_service
from app.services.external_verifier import external_verifier
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
    MailScope Layered Technical Non-Delivery Email Verification Engine.
    Executes a 5-step evidence-based inspection pipeline WITHOUT sending emails or OTPs:
    STEP 1: EMAIL FORMAT / SYNTAX
    STEP 2: DOMAIN VALIDATION (DNS A/AAAA)
    STEP 3: MX RECORD CHECK
    STEP 4: SMTP HANDSHAKE & RCPT TO RECIPIENT PROBE
    STEP 5: EVIDENCE AGGREGATION & FINAL RESULT CLASSIFICATION
    """

    def validateSyntax(self, raw_email: str) -> Dict[str, Any]:
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
        if not domain or "." not in domain or domain.startswith(".") or domain.endswith(".") or domain.startswith("-") or domain.endswith("-"):
            return {
                "passed": False,
                "display_value": "FAIL",
                "message": f"Domain '{domain}' has an invalid format.",
            }

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
                "message": dns_res.get("error") or "Domain does not exist or resolve to active DNS records.",
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
        is_disp = is_disposable_domain(domain)
        return {
            "is_disposable": is_disp,
            "display_value": "YES" if is_disp else "NO",
            "passed": not is_disp,
            "message": "Domain matches a known disposable email provider." if is_disp else "Domain is not identified as a disposable inbox.",
        }

    def detectRoleBased(self, local_part: str) -> Dict[str, Any]:
        is_role = is_role_based_local_part(local_part)
        return {
            "is_role_based": is_role,
            "display_value": "YES" if is_role else "NO",
            "passed": not is_role,
            "message": "Address is role-based (team/department alias)." if is_role else "Address is individual, not a generic role alias.",
        }

    def detectFreeMail(self, domain: str) -> Dict[str, Any]:
        is_free = is_free_email_domain(domain)
        return {
            "is_free_provider": is_free,
            "display_value": "YES" if is_free else "NO",
            "passed": True,
            "message": f"Domain is hosted by consumer provider ({domain})." if is_free else "Domain is a custom/corporate business domain.",
        }

    def determineProviderCapability(self, domain: str, smtp_res: Dict[str, Any]) -> str:
        if smtp_res.get("is_catch_all"):
            return "CATCH_ALL"
        if smtp_res.get("smtp_status") == "ACCEPTED" and smtp_res.get("mailbox_status") == "CONFIRMED":
            return "MAILBOX_VERIFICATION_SUPPORTED"
        if smtp_res.get("smtp_status") == "REJECTED" or smtp_res.get("mailbox_status") in ["NOT_FOUND", "REJECTED"]:
            return "MAILBOX_VERIFICATION_SUPPORTED"
        if smtp_res.get("smtp_status") in ["BLOCKED", "TIMEOUT"]:
            return "MAILBOX_VERIFICATION_RESTRICTED"
        if smtp_res.get("smtp_status") == "GREYLISTED":
            return "TEMPORARY_GREYLISTING"
        return "MAILBOX_VERIFICATION_AMBIGUOUS"

    def evaluateResult(self, signals: Dict[str, Any]) -> Tuple[str, str, int, str, str, str, str, str, str, str, str, str, str]:
        """
        Evaluates signals and returns:
        (status, final_status, score, confidence_level, reason, message,
         email_format, domain_status, mx_status, smtp_connection_status, recipient_status,
         mailbox_evidence, verification_capability, mailbox_existence)
        """
        syntax = signals["syntax"]
        domain = signals["domain"]
        dns = signals["dns"]
        mx = signals["mx"]
        smtp = signals["smtp"]
        disposable = signals["disposable"]
        role_based = signals["role_based"]
        dom_name = signals.get("domain_name", "")

        capability = self.determineProviderCapability(dom_name, smtp)

        # 1. Syntax Fail
        if not syntax["passed"]:
            return (
                "INVALID", "NOT REAL / INVALID", 0, "HIGH",
                "Email address syntax is invalid.", syntax["message"],
                "INVALID", "INVALID", "UNKNOWN", "SKIPPED", "REJECTED",
                "CONFIRMED_REJECTED", capability, "REJECTED"
            )

        # 2. Domain Format Fail
        if not domain["passed"]:
            return (
                "INVALID", "NOT REAL / INVALID", 0, "HIGH",
                "Email address has an invalid domain format.", domain["message"],
                "VALID", "INVALID", "UNKNOWN", "SKIPPED", "REJECTED",
                "CONFIRMED_REJECTED", capability, "REJECTED"
            )

        # 3. DNS Resolution Fail / Timeout
        if not dns["passed"]:
            if dns.get("is_timeout"):
                return (
                    "UNKNOWN", "UNKNOWN", 40, "MEDIUM",
                    "DNS lookup timed out during nameserver resolution.",
                    "DNS query timed out. Mailbox existence cannot be determined without nameserver resolution.",
                    "VALID", "UNKNOWN", "UNKNOWN", "SKIPPED", "UNCONFIRMED",
                    "NO_EVIDENCE", capability, "NOT CONFIRMED"
                )
            return (
                "INVALID", "NOT REAL / INVALID", 0, "HIGH",
                "The email domain does not exist (NXDOMAIN).", dns["message"],
                "VALID", "INVALID", "MISSING", "SKIPPED", "REJECTED",
                "CONFIRMED_REJECTED", capability, "REJECTED"
            )

        # 4. MX Record Fail / Timeout
        if not mx["passed"]:
            if mx.get("is_timeout"):
                return (
                    "UNKNOWN", "UNKNOWN", 45, "MEDIUM",
                    "MX lookup timed out while checking mail server configuration.",
                    "MX DNS query timed out. Mail server configuration could not be verified.",
                    "VALID", "VALID", "UNKNOWN", "SKIPPED", "UNCONFIRMED",
                    "NO_EVIDENCE", capability, "NOT CONFIRMED"
                )
            return (
                "INVALID", "NOT REAL / INVALID", 0, "HIGH",
                "No mail exchange (MX) servers configured for this domain.", mx["message"],
                "VALID", "VALID", "MISSING", "SKIPPED", "REJECTED",
                "CONFIRMED_REJECTED", capability, "REJECTED"
            )

        # 5. Explicit SMTP Recipient Rejection (550 User Unknown / 551 / 553)
        if smtp["smtp_status"] == "REJECTED" or smtp["mailbox_status"] in ["NOT_FOUND", "REJECTED"]:
            server_msg = smtp.get("server_message") or "Destination mail server rejected target recipient address."
            return (
                "INVALID", "NOT REAL / INVALID", 0, "HIGH",
                f"The email format is valid, but the receiving SMTP server explicitly rejected recipient: {server_msg}",
                server_msg,
                "VALID", "VALID", "FOUND", "CONNECTED" if smtp.get("connected") else "BLOCKED", "REJECTED",
                "CONFIRMED_REJECTED", capability, "REJECTED"
            )

        # 6. Risk Signal 1: Disposable Domain
        if disposable["is_disposable"]:
            return (
                "RISKY", "RISKY", 30, "HIGH",
                "Domain matches a known disposable temporary email provider.",
                "Email address syntax and domain are valid, but it belongs to a temporary/disposable inbox provider.",
                "VALID", "VALID", "FOUND", "CONNECTED" if smtp.get("connected") else "BLOCKED", "UNCONFIRMED",
                "ACCEPTED_NOT_CONFIRMED", capability, "NOT CONFIRMED"
            )

        # 7. Risk Signal 2: Catch-All Domain
        if smtp.get("is_catch_all"):
            return (
                "RISKY", "RISKY", 60, "MEDIUM",
                "The receiving mail server accepts arbitrary recipients (Catch-All), so the existence of this specific mailbox cannot be independently confirmed.",
                "Destination mail server operates Catch-All mail routing and accepts any recipient prefix. Specific mailbox existence cannot be guaranteed.",
                "VALID", "VALID", "FOUND", "CONNECTED", "CATCH_ALL",
                "CATCH_ALL", "CATCH_ALL", "NOT CONFIRMED"
            )

        # 8. Risk Signal 3: Role-Based Alias
        if role_based["is_role_based"]:
            return (
                "RISKY", "RISKY", 65, "MEDIUM",
                "Address is role-based (department alias e.g. info, support, admin).",
                "Email address appears technically functional but is a department/role alias rather than a personal mailbox.",
                "VALID", "VALID", "FOUND", "CONNECTED" if smtp.get("connected") else "BLOCKED", "UNCONFIRMED",
                "ACCEPTED_NOT_CONFIRMED", capability, "NOT CONFIRMED"
            )

        # 9. SMTP Accepted Recipient & Confirmed Non-Catch-All (REAL / VALID)
        if smtp["smtp_status"] == "ACCEPTED" and smtp["mailbox_status"] == "CONFIRMED":
            server_msg = smtp.get("server_message") or "Mailbox recipient accepted by server (250 OK)."
            return (
                "VALID", "REAL / VALID", 95, "HIGH",
                f"SMTP recipient-level verification confirmed recipient existence: {server_msg}",
                "Email address passed all technical syntax, DNS, MX, and recipient mailbox non-delivery checks.",
                "VALID", "VALID", "FOUND", "CONNECTED", "ACCEPTED",
                "CONFIRMED_EXISTS", "MAILBOX_VERIFICATION_SUPPORTED", "CONFIRMED"
            )

        # 10. SMTP Restriction / Greylisting / Timeout / Inconclusive (UNKNOWN)
        smtp_status = smtp.get("smtp_status", "UNKNOWN")
        smtp_conn_str = "CONNECTED" if smtp.get("connected") else ("TIMEOUT" if smtp_status == "TIMEOUT" else "BLOCKED")
        server_msg = smtp.get("server_message") or ""
        free_mail = signals.get("free_mail", {})

        if free_mail.get("is_free_provider"):
            mx_count = len(mx.get("mx_records", []))
            primary_host = mx.get("primary_host") or "mail server"
            reason = f"Domain mail infrastructure is active ({mx_count} MX records, Primary: {primary_host}). However, {dom_name} protects against automated recipient scraping, so the existence of this specific mailbox cannot be confirmed without sending an email."
            msg = f"Infrastructure is active and deliverable, but {dom_name} restricts non-contact mailbox existence probing."
            score = 75
            evidence = "NO_EVIDENCE"
            capability = "MAILBOX_VERIFICATION_RESTRICTED"
        elif smtp_status == "GREYLISTED":
            reason = f"Destination mail server returned temporary greylisting/rate-limit response: {server_msg}"
            msg = "Mail server responded with a temporary 4xx code. Try again later."
            score = 60
            evidence = "AMBIGUOUS"
            capability = "TEMPORARY_GREYLISTING"
        elif smtp_status == "TIMEOUT":
            reason = f"Outbound SMTP connection timed out: {server_msg}"
            msg = "Connection to mail server timed out on Port 25. Mailbox existence is unconfirmed."
            score = 50
            evidence = "TIMEOUT"
            capability = "MAILBOX_VERIFICATION_RESTRICTED"
        elif smtp_status == "BLOCKED":
            reason = f"Outbound SMTP connection restricted: {server_msg}"
            msg = "Port 25 outbound network connection was blocked or restricted by hosting provider."
            score = 50
            evidence = "PROVIDER_BLOCKED"
            capability = "MAILBOX_VERIFICATION_RESTRICTED"
        else:
            reason = f"Ambiguous SMTP response: {server_msg}" if server_msg else "Receiving mail server did not disclose recipient mailbox status."
            msg = "The receiving mail server did not provide explicit mailbox confirmation."
            score = 50
            evidence = "NO_EVIDENCE"
            capability = "MAILBOX_VERIFICATION_AMBIGUOUS"

        return (
            "UNKNOWN", "UNKNOWN", score, "MEDIUM",
            reason, msg,
            "VALID", "VALID", "FOUND", smtp_conn_str, "UNCONFIRMED",
            evidence, capability, "NOT CONFIRMED"
        )

    def verify_email(self, email: str) -> VerifyResponse:
        t_start = time.perf_counter()
        raw_email = (email or "").strip()

        # 1. Syntax Validation
        t_syn_0 = time.perf_counter()
        syntax_res = self.validateSyntax(raw_email)
        t_syn_1 = time.perf_counter()
        syntax_time_ms = round((t_syn_1 - t_syn_0) * 1000, 2)

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
        t_dns_0 = time.perf_counter()
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
        t_dns_1 = time.perf_counter()
        dns_time_ms = round((t_dns_1 - t_dns_0) * 1000, 2) if domain_res["passed"] else 0.0

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

        # 8. Server-Side SMTP Non-Delivery Probing
        t_smtp_0 = time.perf_counter()
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
        t_smtp_1 = time.perf_counter()
        smtp_time_ms = round((t_smtp_1 - t_smtp_0) * 1000, 2) if mx_res["passed"] else 0.0

        # Optional External Verification Provider Adapter
        ext_res = external_verifier.verify_email_external(normalized_email)
        if ext_res and ext_res.get("is_valid") is not None:
            if ext_res["is_valid"]:
                smtp_res["smtp_status"] = "ACCEPTED"
                smtp_res["mailbox_status"] = "CONFIRMED"
                smtp_res["server_message"] = "Mailbox verified via authorized verification adapter."
            else:
                smtp_res["smtp_status"] = "REJECTED"
                smtp_res["mailbox_status"] = "NOT_FOUND"
                smtp_res["server_message"] = "Mailbox rejected via authorized verification adapter."

        # Aggregate Signals
        signals = {
            "syntax": syntax_res,
            "domain": domain_res,
            "dns": dns_res,
            "mx": mx_res,
            "smtp": smtp_res,
            "disposable": disp_res,
            "role_based": role_res,
            "free_mail": free_res,
            "domain_name": domain,
        }

        # Evaluate Technical Results
        (
            status, final_status, score, confidence_level, reason, message,
            email_format, domain_status, mx_status, smtp_conn_status, recipient_status,
            mb_evidence, cap_status, mb_existence
        ) = self.evaluateResult(signals)

        # Risk Signals List
        risk_signals = []
        if disp_res["is_disposable"]:
            risk_signals.append("DISPOSABLE_TEMPORARY_DOMAIN")
        if smtp_res.get("is_catch_all"):
            risk_signals.append("CATCH_ALL_MAIL_ROUTING")
        if role_res["is_role_based"]:
            risk_signals.append("ROLE_BASED_ALIAS")

        primary_mx = mx_res.get("mx_records", [{}])[0].get("host") if mx_res.get("mx_records") else None

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
        mailbox_display_val = mailbox_display_map.get(smtp_res.get("mailbox_status"), "UNCONFIRMED")

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
                passed=mb_existence == "CONFIRMED",
                status=mailbox_display_val,
                display_value=mailbox_display_val,
                message=(
                    "Mailbox existence confirmed by destination mail server (250 OK)." if mb_existence == "CONFIRMED" else (
                        "Mailbox rejected by destination mail server (550)." if mb_existence == "REJECTED" else
                        "Mailbox existence could not be confirmed via SMTP probing."
                    )
                ),
                details={"status": mb_existence, "is_catch_all": smtp_res.get("is_catch_all", False)}
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

        # Map classification string
        classification_map = {
            "VALID": "REAL",
            "INVALID": "INVALID",
            "RISKY": "RISKY",
            "UNKNOWN": "UNKNOWN"
        }
        classification = classification_map.get(status, "UNKNOWN")

        # Prepare structured SMTP summary
        smtp_trace_dict = smtp_res.get("smtp_trace") or {}
        smtp_summary = {
            "attempted": smtp_res.get("attempted", False),
            "connected": smtp_res.get("connected", False),
            "mx_host": smtp_res.get("mx_host_used") or primary_mx,
            "ehlo": smtp_trace_dict.get("ehlo"),
            "mail_from": smtp_trace_dict.get("mail_from"),
            "rcpt_to": smtp_trace_dict.get("rcpt_to"),
            "data_sent": False
        }

        total_time_ms = round((time.perf_counter() - t_start) * 1000, 2)
        perf_metrics = {
            "syntax_time_ms": syntax_time_ms,
            "dns_time_ms": dns_time_ms,
            "smtp_time_ms": smtp_time_ms,
            "total_time_ms": total_time_ms
        }

        display_final_status = "REAL / REACHABLE" if status == "VALID" else final_status

        return VerifyResponse(
            email=raw_email,
            normalized_email=normalized_email,
            domain=domain,
            status=status,
            final_status=display_final_status,
            classification=classification,
            score=score,
            confidence=score,
            confidence_level=confidence_level,
            verification_method="NON_CONTACT_SMTP",
            notification_sent=False,
            data_sent=False,
            performance_metrics=perf_metrics,
            email_format=email_format,
            domain_status=domain_status,
            mx_status=mx_status,
            smtp_connection_status=smtp_conn_status,
            recipient_status=recipient_status,
            syntax_valid=syntax_res["passed"],
            domain_exists=domain_res["passed"],
            dns_resolved=dns_res["passed"],
            mx_found=mx_res["passed"],
            mx_host=primary_mx,
            smtp_connection=smtp_res.get("connected", False),
            smtp_recipient_response=smtp_res.get("server_message"),
            mailbox_evidence=mb_evidence,
            verification_capability=cap_status,
            mailbox_existence=mb_existence,
            catch_all_detected=smtp_res.get("is_catch_all", False),
            disposable_detected=disp_res["is_disposable"],
            role_account_detected=role_res["is_role_based"],
            risk_signals=risk_signals,
            smtp=smtp_summary,
            smtp_trace=smtp_res.get("smtp_trace"),
            checks=checks,
            domain_intelligence=domain_intel,
            message=message,
            reason=reason,
        )

verification_service = VerificationEngine()

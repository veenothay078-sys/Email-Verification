import smtplib
import socket
import uuid
from typing import Dict, Any, List, Optional
from app.core.config import settings

class SMTPVerificationService:
    def __init__(self, timeout: float = 2.0, sender_domain: str = "openmail.verify"):
        self.timeout = timeout
        self.sender_domain = sender_domain
        self.sender_email = f"verify@{sender_domain}"

    def verify_mailbox_smtp(self, email: str, domain: str, mx_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Safely performs server-side SMTP recipient verification (EHLO, MAIL FROM, RCPT TO).
        Uses strict 2.0s timeout to guarantee instant response even if port 25 is filtered.
        Does NOT send any actual email message.
        """
        result = {
            "attempted": False,
            "connected": False,
            "smtp_status": "SKIPPED", # ACCEPTED, REJECTED, BLOCKED, TIMEOUT, GREYLISTED, UNKNOWN
            "mailbox_status": "UNCONFIRMED", # CONFIRMED, NOT_FOUND, UNCONFIRMED, CATCH_ALL
            "is_catch_all": False,
            "server_code": None,
            "server_message": "",
            "mx_host_used": None,
            "details": {}
        }

        if not email or not domain or not mx_records:
            result["server_message"] = "No MX records available to establish SMTP connection."
            return result

        result["attempted"] = True
        
        # Test primary MX host
        primary_mx = mx_records[0].get("host")
        if not primary_mx:
            return result

        try:
            return self._probe_smtp_host(primary_mx, email, domain)
        except Exception as e:
            return {
                "attempted": True,
                "connected": False,
                "smtp_status": "BLOCKED",
                "mailbox_status": "UNCONFIRMED",
                "is_catch_all": False,
                "server_code": None,
                "server_message": f"SMTP probe could not complete ({primary_mx}): {str(e)[:100]}",
                "mx_host_used": primary_mx,
                "details": {"error": str(e)}
            }

    def _probe_smtp_host(self, mx_host: str, target_email: str, domain: str) -> Dict[str, Any]:
        sock = None
        server = None
        try:
            # Explicit fast socket connection on port 25 with timeout
            sock = socket.create_connection((mx_host, 25), timeout=self.timeout)
            sock.settimeout(self.timeout)
            
            server = smtplib.SMTP()
            server.sock = sock
            
            # Read server greeting
            code, msg = server.getreply()
            if code >= 400:
                return {
                    "attempted": True,
                    "connected": True,
                    "smtp_status": "BLOCKED" if code >= 500 else "GREYLISTED",
                    "mailbox_status": "UNCONFIRMED",
                    "is_catch_all": False,
                    "server_code": code,
                    "server_message": f"Server connection restricted ({code}): {msg.decode('utf-8', 'ignore') if isinstance(msg, bytes) else str(msg)}",
                    "mx_host_used": mx_host,
                    "details": {"stage": "CONNECT", "code": code}
                }

            # Issue EHLO / HELO
            try:
                server.ehlo_or_helo_if_needed()
            except Exception:
                pass

            # Issue MAIL FROM
            mail_code, mail_msg = server.mail(self.sender_email)
            if mail_code >= 400:
                return {
                    "attempted": True,
                    "connected": True,
                    "smtp_status": "BLOCKED",
                    "mailbox_status": "UNCONFIRMED",
                    "is_catch_all": False,
                    "server_code": mail_code,
                    "server_message": f"MAIL FROM unaccepted by provider ({mail_code}). Mailbox unconfirmed.",
                    "mx_host_used": mx_host,
                    "details": {"stage": "MAIL_FROM", "code": mail_code}
                }

            # Issue RCPT TO for the target email
            rcpt_code, rcpt_msg = server.rcpt(target_email)
            rcpt_msg_str = rcpt_msg.decode('utf-8', 'ignore') if isinstance(rcpt_msg, bytes) else str(rcpt_msg)

            # Analyze recipient response
            if rcpt_code == 250 or rcpt_code == 251:
                # Check for Catch-All domain: probe an impossible random address
                is_catch_all = False
                try:
                    random_user = f"probe_check_{uuid.uuid4().hex[:8]}"
                    random_email = f"{random_user}@{domain}"
                    random_code, _ = server.rcpt(random_email)
                    if random_code == 250:
                        is_catch_all = True
                except Exception:
                    pass

                return {
                    "attempted": True,
                    "connected": True,
                    "smtp_status": "ACCEPTED",
                    "mailbox_status": "CATCH_ALL" if is_catch_all else "CONFIRMED",
                    "is_catch_all": is_catch_all,
                    "server_code": rcpt_code,
                    "server_message": "Domain operates Catch-All mail routing." if is_catch_all else "Mailbox confirmed by destination mail server (250 OK).",
                    "mx_host_used": mx_host,
                    "details": {"stage": "RCPT_TO", "code": rcpt_code, "raw_reply": rcpt_msg_str}
                }

            elif rcpt_code in [550, 551, 552, 553, 554]:
                # Definite recipient rejection / User unknown
                return {
                    "attempted": True,
                    "connected": True,
                    "smtp_status": "REJECTED",
                    "mailbox_status": "NOT_FOUND",
                    "is_catch_all": False,
                    "server_code": rcpt_code,
                    "server_message": f"Mailbox rejected by destination server ({rcpt_code}): {rcpt_msg_str}",
                    "mx_host_used": mx_host,
                    "details": {"stage": "RCPT_TO", "code": rcpt_code, "raw_reply": rcpt_msg_str}
                }

            elif rcpt_code in [421, 450, 451, 452]:
                # Temporary greylisting
                return {
                    "attempted": True,
                    "connected": True,
                    "smtp_status": "GREYLISTED",
                    "mailbox_status": "UNCONFIRMED",
                    "is_catch_all": False,
                    "server_code": rcpt_code,
                    "server_message": f"Temporary greylisting from mail provider ({rcpt_code}). Mailbox unconfirmed.",
                    "mx_host_used": mx_host,
                    "details": {"stage": "RCPT_TO", "code": rcpt_code, "raw_reply": rcpt_msg_str}
                }

            else:
                return {
                    "attempted": True,
                    "connected": True,
                    "smtp_status": "UNKNOWN",
                    "mailbox_status": "UNCONFIRMED",
                    "is_catch_all": False,
                    "server_code": rcpt_code,
                    "server_message": f"Inconclusive SMTP response code ({rcpt_code}).",
                    "mx_host_used": mx_host,
                    "details": {"stage": "RCPT_TO", "code": rcpt_code, "raw_reply": rcpt_msg_str}
                }

        except (socket.timeout, TimeoutError):
            return {
                "attempted": True,
                "connected": False,
                "smtp_status": "TIMEOUT",
                "mailbox_status": "UNCONFIRMED",
                "is_catch_all": False,
                "server_code": None,
                "server_message": f"SMTP connection to {mx_host}:25 timed out (port 25 filtered). Mailbox unconfirmed.",
                "mx_host_used": mx_host,
                "details": {"error": "Connection timed out"}
            }

        except (ConnectionRefusedError, socket.gaierror, OSError) as e:
            return {
                "attempted": True,
                "connected": False,
                "smtp_status": "BLOCKED",
                "mailbox_status": "UNCONFIRMED",
                "is_catch_all": False,
                "server_code": None,
                "server_message": f"Port 25 outbound restricted by network/firewall for {mx_host}. Mailbox unconfirmed.",
                "mx_host_used": mx_host,
                "details": {"error": str(e)}
            }

        finally:
            if server:
                try:
                    server.close()
                except Exception:
                    pass
            elif sock:
                try:
                    sock.close()
                except Exception:
                    pass

smtp_service = SMTPVerificationService(timeout=2.0)

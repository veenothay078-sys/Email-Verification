import smtplib
import socket
import uuid
import logging
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger("mailscope.smtp")

class SMTPVerificationService:
    def __init__(self, timeout: float = 3.0, sender_domain: str = None, sender_email: str = None):
        self.timeout = timeout
        self.sender_domain = sender_domain if sender_domain is not None else settings.SMTP_HELO_DOMAIN
        self.sender_email = sender_email if sender_email is not None else settings.VERIFIER_MAIL_FROM

    def verify_mailbox_smtp(self, email: str, domain: str, mx_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Safely performs server-side SMTP recipient verification (EHLO, MAIL FROM, RCPT TO).
        Connects to destination MX hosts on Port 25 in priority order.
        Preserves full trace of all attempted MX servers.
        Does NOT send any actual email message or issue DATA commands.
        """
        attempted_servers = []
        result = {
            "attempted": False,
            "connected": False,
            "smtp_status": "SKIPPED", # ACCEPTED, REJECTED, BLOCKED, TIMEOUT, GREYLISTED, UNKNOWN
            "mailbox_status": "UNCONFIRMED", # CONFIRMED, NOT_FOUND, UNCONFIRMED, CATCH_ALL
            "is_catch_all": False,
            "server_code": None,
            "server_message": "",
            "mx_host_used": None,
            "data_sent": False,
            "smtp_trace": {
                "attempted": False,
                "connected": False,
                "hostname": None,
                "mx_host": None,
                "port": 25,
                "stage": "SKIPPED",
                "greeting": None,
                "ehlo": None,
                "mail_from": None,
                "rcpt_to": None,
                "data_sent": False,
                "catch_all_probe": None,
                "attempted_servers": []
            },
            "details": {}
        }

        if not email or not domain or not mx_records:
            result["server_message"] = "No MX records available to establish SMTP connection."
            return result

        result["attempted"] = True

        # Sort MX records by priority ascending (5, 10, 20...)
        sorted_mx = sorted(mx_records, key=lambda x: x.get("priority", 10))

        # Test primary MX hosts in order of priority (up to top 3)
        probe_res = None
        for mx_entry in sorted_mx[:3]:
            mx_host = mx_entry.get("host")
            if not mx_host:
                continue

            probe_res = self._probe_smtp_host(mx_host, email, domain, attempted_servers)
            # If connected successfully and obtained a recipient status, return immediately
            if probe_res.get("connected"):
                probe_res["smtp_trace"]["attempted_servers"] = attempted_servers
                return probe_res
            result = probe_res

        if probe_res:
            probe_res["smtp_trace"]["attempted_servers"] = attempted_servers
            return probe_res

        result["smtp_trace"]["attempted_servers"] = attempted_servers
        return result

    def _probe_smtp_host(
        self,
        mx_host: str,
        target_email: str,
        domain: str,
        attempted_servers_log: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        sock = None
        server = None

        logger.info(f"[SMTP] Target: {target_email}")
        logger.info(f"[SMTP] MX: {mx_host}")
        logger.info(f"[SMTP] Connecting...")

        server_trace = {
            "host": mx_host,
            "port": 25,
            "connected": False,
            "stage": "CONNECT",
            "greeting": None,
            "ehlo": None,
            "mail_from": None,
            "rcpt_to": None,
            "data_sent": False,
            "catch_all_probe": None,
            "error": None
        }

        try:
            # 1. Dual-Stack TCP Socket Connection on Port 25 (IPv6 / IPv4 fast fallback)
            sock = None
            last_conn_err = None
            try:
                addresses = socket.getaddrinfo(mx_host, 25, socket.AF_UNSPEC, socket.SOCK_STREAM)
                for res in addresses:
                    af, socktype, proto, canonname, sa = res
                    s = None
                    try:
                        s = socket.socket(af, socktype, proto)
                        s.settimeout(1.2)
                        s.connect(sa)
                        sock = s
                        sock.settimeout(self.timeout)
                        break
                    except Exception as err:
                        if s:
                            s.close()
                        last_conn_err = err
            except Exception as gai_err:
                last_conn_err = gai_err

            if not sock:
                try:
                    sock = socket.create_connection((mx_host, 25), timeout=self.timeout)
                    sock.settimeout(self.timeout)
                except Exception as fallback_err:
                    raise last_conn_err or fallback_err

            server = smtplib.SMTP()
            server.sock = sock
            server_trace["connected"] = True
            server_trace["stage"] = "GREETING"

            # 2. Read Server Greeting Banner
            code, msg = server.getreply()
            greeting_str = msg.decode('utf-8', 'ignore') if isinstance(msg, bytes) else str(msg)
            server_trace["greeting"] = {"code": code, "status_code": code, "response": greeting_str}
            logger.info(f"[SMTP] Greeting: {code} {greeting_str}")

            if code >= 400:
                logger.info(f"[SMTP] DATA SENT: false")
                logger.info(f"[SMTP] QUIT")
                logger.info(f"[RESULT] UNKNOWN")
                server_trace["stage"] = "GREETING"
                server_trace["error"] = f"Greeting rejected ({code}): {greeting_str}"
                attempted_servers_log.append(server_trace)
                return {
                    "attempted": True,
                    "connected": True,
                    "smtp_status": "BLOCKED" if code >= 500 else "GREYLISTED",
                    "mailbox_status": "UNCONFIRMED",
                    "is_catch_all": False,
                    "server_code": code,
                    "server_message": f"Server connection restricted during greeting ({code}): {greeting_str}",
                    "mx_host_used": mx_host,
                    "data_sent": False,
                    "smtp_trace": {
                        "attempted": True,
                        "connected": True,
                        "hostname": mx_host,
                        "mx_host": mx_host,
                        "port": 25,
                        "stage": "GREETING",
                        "greeting": {"code": code, "status_code": code, "response": greeting_str},
                        "ehlo": None,
                        "mail_from": None,
                        "rcpt_to": None,
                        "data_sent": False,
                        "catch_all_probe": None,
                        "attempted_servers": attempted_servers_log
                    },
                    "details": {"stage": "GREETING", "code": code, "msg": greeting_str}
                }

            # 3. Issue EHLO / HELO
            server_trace["stage"] = "EHLO"
            ehlo_code = 250
            ehlo_msg_str = "250 OK"
            try:
                ehlo_code, ehlo_msg = server.ehlo(self.sender_domain)
                ehlo_msg_str = ehlo_msg.decode('utf-8', 'ignore') if isinstance(ehlo_msg, bytes) else str(ehlo_msg)
            except Exception as ehlo_err:
                try:
                    server.helo(self.sender_domain)
                except Exception:
                    pass
            server_trace["ehlo"] = {"code": ehlo_code, "status_code": ehlo_code, "response": ehlo_msg_str}
            logger.info(f"[SMTP] EHLO: {ehlo_code}")

            # 4. Issue MAIL FROM
            server_trace["stage"] = "MAIL_FROM"
            mail_code, mail_msg = server.mail(self.sender_email)
            mail_msg_str = mail_msg.decode('utf-8', 'ignore') if isinstance(mail_msg, bytes) else str(mail_msg)
            server_trace["mail_from"] = {"code": mail_code, "status_code": mail_code, "response": mail_msg_str}
            logger.info(f"[SMTP] MAIL FROM: {mail_code}")

            if mail_code >= 400:
                logger.info(f"[SMTP] DATA SENT: false")
                logger.info(f"[SMTP] QUIT")
                logger.info(f"[RESULT] UNKNOWN")
                server_trace["error"] = f"MAIL FROM rejected ({mail_code}): {mail_msg_str}"
                attempted_servers_log.append(server_trace)
                return {
                    "attempted": True,
                    "connected": True,
                    "smtp_status": "BLOCKED" if mail_code >= 500 else "GREYLISTED",
                    "mailbox_status": "UNCONFIRMED",
                    "is_catch_all": False,
                    "server_code": mail_code,
                    "server_message": f"MAIL FROM sender address rejected by server ({mail_code}): {mail_msg_str}",
                    "mx_host_used": mx_host,
                    "data_sent": False,
                    "smtp_trace": {
                        "attempted": True,
                        "connected": True,
                        "hostname": mx_host,
                        "mx_host": mx_host,
                        "port": 25,
                        "stage": "MAIL_FROM",
                        "greeting": {"code": code, "status_code": code, "response": greeting_str},
                        "ehlo": {"code": ehlo_code, "status_code": ehlo_code, "response": ehlo_msg_str},
                        "mail_from": {"code": mail_code, "status_code": mail_code, "response": mail_msg_str},
                        "rcpt_to": None,
                        "data_sent": False,
                        "catch_all_probe": None,
                        "attempted_servers": attempted_servers_log
                    },
                    "details": {"stage": "MAIL_FROM", "code": mail_code, "msg": mail_msg_str}
                }

            # 5. Issue RCPT TO for Target Recipient
            server_trace["stage"] = "RCPT_TO"
            rcpt_code, rcpt_msg = server.rcpt(target_email)
            rcpt_msg_str = rcpt_msg.decode('utf-8', 'ignore') if isinstance(rcpt_msg, bytes) else str(rcpt_msg)
            server_trace["rcpt_to"] = {"code": rcpt_code, "status_code": rcpt_code, "response": rcpt_msg_str}

            logger.info(f"[SMTP] RCPT TO: {rcpt_code} {rcpt_msg_str}")
            logger.info(f"[SMTP] DATA SENT: false")
            logger.info(f"[SMTP] QUIT")

            # 6. Analyze Recipient Response
            if rcpt_code == 250 or rcpt_code == 251:
                logger.info(f"[RESULT] SMTP_ACCEPTED")
                # Catch-All Detection Probe
                is_catch_all = False
                random_code = None
                random_msg_str = None
                try:
                    random_user = f"mailscope_random_{uuid.uuid4().hex[:8]}"
                    random_email = f"{random_user}@{domain}"
                    random_code, random_msg = server.rcpt(random_email)
                    random_msg_str = random_msg.decode('utf-8', 'ignore') if isinstance(random_msg, bytes) else str(random_msg)
                    if random_code == 250 or random_code == 251:
                        is_catch_all = True
                except Exception as catch_err:
                    pass

                catch_all_trace = {
                    "tested": random_code is not None,
                    "code": random_code,
                    "response": random_msg_str,
                    "is_catch_all": is_catch_all
                }
                server_trace["catch_all_probe"] = catch_all_trace

                # Cleanly reset and quit without issuing DATA
                try:
                    server.rset()
                    server.quit()
                except Exception:
                    pass

                attempted_servers_log.append(server_trace)
                return {
                    "attempted": True,
                    "connected": True,
                    "smtp_status": "ACCEPTED",
                    "mailbox_status": "CATCH_ALL" if is_catch_all else "CONFIRMED",
                    "is_catch_all": is_catch_all,
                    "server_code": rcpt_code,
                    "server_message": f"Receiving server accepts arbitrary recipients, so individual mailbox existence cannot be confirmed." if is_catch_all else f"Mailbox recipient accepted by destination mail server ({rcpt_code} OK): {rcpt_msg_str}",
                    "mx_host_used": mx_host,
                    "data_sent": False,
                    "smtp_trace": {
                        "attempted": True,
                        "connected": True,
                        "hostname": mx_host,
                        "mx_host": mx_host,
                        "port": 25,
                        "stage": "RCPT_TO",
                        "greeting": {"code": code, "status_code": code, "response": greeting_str},
                        "ehlo": {"code": ehlo_code, "status_code": ehlo_code, "response": ehlo_msg_str},
                        "mail_from": {"code": mail_code, "status_code": mail_code, "response": mail_msg_str},
                        "rcpt_to": {"code": rcpt_code, "status_code": rcpt_code, "response": rcpt_msg_str, "attempted": True},
                        "data_sent": False,
                        "catch_all_probe": catch_all_trace,
                        "attempted_servers": attempted_servers_log
                    },
                    "details": {"stage": "RCPT_TO", "code": rcpt_code, "raw_reply": rcpt_msg_str, "is_catch_all": is_catch_all}
                }

            elif rcpt_code in [550, 551, 552, 553, 554]:
                logger.info(f"[RESULT] INVALID")
                # Permanent recipient rejection / User unknown
                try:
                    server.rset()
                    server.quit()
                except Exception:
                    pass

                attempted_servers_log.append(server_trace)
                return {
                    "attempted": True,
                    "connected": True,
                    "smtp_status": "REJECTED",
                    "mailbox_status": "NOT_FOUND",
                    "is_catch_all": False,
                    "server_code": rcpt_code,
                    "server_message": f"Mailbox explicitly rejected by destination server ({rcpt_code}): {rcpt_msg_str}",
                    "mx_host_used": mx_host,
                    "data_sent": False,
                    "smtp_trace": {
                        "attempted": True,
                        "connected": True,
                        "hostname": mx_host,
                        "mx_host": mx_host,
                        "port": 25,
                        "stage": "RCPT_TO",
                        "greeting": {"code": code, "status_code": code, "response": greeting_str},
                        "ehlo": {"code": ehlo_code, "status_code": ehlo_code, "response": ehlo_msg_str},
                        "mail_from": {"code": mail_code, "status_code": mail_code, "response": mail_msg_str},
                        "rcpt_to": {"code": rcpt_code, "status_code": rcpt_code, "response": rcpt_msg_str, "attempted": True},
                        "data_sent": False,
                        "catch_all_probe": None,
                        "attempted_servers": attempted_servers_log
                    },
                    "details": {"stage": "RCPT_TO", "code": rcpt_code, "raw_reply": rcpt_msg_str}
                }

            elif rcpt_code in [421, 450, 451, 452]:
                # Temporary greylisting or rate limiting
                try:
                    server.quit()
                except Exception:
                    pass

                attempted_servers_log.append(server_trace)
                return {
                    "attempted": True,
                    "connected": True,
                    "smtp_status": "GREYLISTED",
                    "mailbox_status": "UNCONFIRMED",
                    "is_catch_all": False,
                    "server_code": rcpt_code,
                    "server_message": f"Temporary greylisting/rate limiting response from mail server ({rcpt_code}): {rcpt_msg_str}",
                    "mx_host_used": mx_host,
                    "smtp_trace": {
                        "attempted": True,
                        "connected": True,
                        "hostname": mx_host,
                        "port": 25,
                        "stage": "RCPT_TO",
                        "greeting": {"code": code, "response": greeting_str},
                        "mail_from": {"code": mail_code, "response": mail_msg_str},
                        "rcpt_to": {"code": rcpt_code, "response": rcpt_msg_str},
                        "catch_all_probe": None,
                        "attempted_servers": attempted_servers_log
                    },
                    "details": {"stage": "RCPT_TO", "code": rcpt_code, "raw_reply": rcpt_msg_str}
                }

            else:
                try:
                    server.quit()
                except Exception:
                    pass

                attempted_servers_log.append(server_trace)
                return {
                    "attempted": True,
                    "connected": True,
                    "smtp_status": "UNKNOWN",
                    "mailbox_status": "UNCONFIRMED",
                    "is_catch_all": False,
                    "server_code": rcpt_code,
                    "server_message": f"Ambiguous SMTP response code ({rcpt_code}): {rcpt_msg_str}",
                    "mx_host_used": mx_host,
                    "smtp_trace": {
                        "attempted": True,
                        "connected": True,
                        "hostname": mx_host,
                        "port": 25,
                        "stage": "RCPT_TO",
                        "greeting": {"code": code, "response": greeting_str},
                        "mail_from": {"code": mail_code, "response": mail_msg_str},
                        "rcpt_to": {"code": rcpt_code, "response": rcpt_msg_str},
                        "catch_all_probe": None,
                        "attempted_servers": attempted_servers_log
                    },
                    "details": {"stage": "RCPT_TO", "code": rcpt_code, "raw_reply": rcpt_msg_str}
                }

        except (socket.timeout, TimeoutError) as t_err:
            logger.info(f"RAW SMTP DEBUG | MX={mx_host} | CONNECT_TIMEOUT on port 25")
            server_trace["error"] = "Connection timed out on Port 25"
            attempted_servers_log.append(server_trace)
            return {
                "attempted": True,
                "connected": False,
                "smtp_status": "TIMEOUT",
                "mailbox_status": "UNCONFIRMED",
                "is_catch_all": False,
                "server_code": None,
                "server_message": f"SMTP socket connection to {mx_host}:25 timed out after {self.timeout}s.",
                "mx_host_used": mx_host,
                "smtp_trace": {
                    "attempted": True,
                    "connected": False,
                    "hostname": mx_host,
                    "port": 25,
                    "stage": "CONNECT_TIMEOUT",
                    "greeting": None,
                    "mail_from": None,
                    "rcpt_to": None,
                    "catch_all_probe": None,
                    "attempted_servers": attempted_servers_log
                },
                "details": {"error": f"Socket connection to {mx_host}:25 timed out."}
            }

        except (ConnectionRefusedError, socket.gaierror, OSError) as e:
            logger.info(f"RAW SMTP DEBUG | MX={mx_host} | CONNECT_ERROR={e}")
            server_trace["error"] = f"Connection error: {str(e)}"
            attempted_servers_log.append(server_trace)
            return {
                "attempted": True,
                "connected": False,
                "smtp_status": "BLOCKED",
                "mailbox_status": "UNCONFIRMED",
                "is_catch_all": False,
                "server_code": None,
                "server_message": f"Outbound Port 25 network restriction or connection error for {mx_host}: {str(e)}",
                "mx_host_used": mx_host,
                "smtp_trace": {
                    "attempted": True,
                    "connected": False,
                    "hostname": mx_host,
                    "port": 25,
                    "stage": "CONNECT_ERROR",
                    "greeting": None,
                    "mail_from": None,
                    "rcpt_to": None,
                    "catch_all_probe": None,
                    "attempted_servers": attempted_servers_log
                },
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

smtp_service = SMTPVerificationService()

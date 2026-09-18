import pytest
from unittest.mock import patch, MagicMock
from app.services.verification_service import verification_service
from app.services.smtp_service import SMTPVerificationService
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_case_1_clearly_valid_gmail():
    res = verification_service.verify_email("john.smith@gmail.com")
    assert res.checks.syntax.passed is True
    assert res.checks.domain.passed is True
    assert res.checks.dns.passed is True
    assert res.checks.mx.passed is True
    assert res.status in ["VALID", "UNKNOWN", "INVALID"]
    assert res.notification_sent is False

def test_case_2_clearly_valid_outlook():
    res = verification_service.verify_email("sarah.connor@outlook.com")
    assert res.checks.syntax.passed is True
    assert res.checks.domain.passed is True
    assert res.checks.dns.passed is True
    assert res.checks.mx.passed is True
    assert res.status in ["VALID", "UNKNOWN"]
    assert res.notification_sent is False

def test_case_3_clearly_malformed_email():
    res = verification_service.verify_email("not-an-email-at-all")
    assert res.status == "INVALID"
    assert res.score == 0
    assert res.confidence_level == "HIGH"
    assert res.checks.syntax.passed is False
    assert res.notification_sent is False

def test_case_4_nonexistent_domain():
    res = verification_service.verify_email("user@nonexistent-domain-xyz-982138.com")
    assert res.status == "INVALID"
    assert res.score == 0
    assert res.confidence_level == "HIGH"
    assert res.checks.dns.passed is False
    assert res.notification_sent is False

def test_case_5_domain_without_mx():
    # Mock DNS service returning A record but no MX
    with patch("app.services.verification_service.dns_service.check_domain_dns") as mock_dns:
        mock_dns.return_value = {
            "domain": "nomxdomain.com",
            "is_resolvable": True,
            "has_mx": False,
            "mx_records": [],
            "a_records": ["1.2.3.4"],
            "error": None,
            "is_timeout": False
        }
        res = verification_service.verify_email("user@nomxdomain.com")
        assert res.status == "INVALID"
        assert res.score == 0
        assert res.checks.mx.passed is False
        assert "No mail exchange" in res.checks.mx.message

def test_case_6_disposable_email_domain():
    res = verification_service.verify_email("testuser@mailinator.com")
    assert res.status == "RISKY"
    assert res.checks.disposable.passed is False
    assert res.checks.disposable.display_value == "YES"

def test_case_7_catch_all_domain():
    # Mock SMTP service returning CATCH_ALL
    with patch("app.services.verification_service.smtp_service.verify_mailbox_smtp") as mock_smtp:
        mock_smtp.return_value = {
            "attempted": True,
            "connected": True,
            "smtp_status": "ACCEPTED",
            "mailbox_status": "CATCH_ALL",
            "is_catch_all": True,
            "server_code": 250,
            "server_message": "Domain operates Catch-All mail routing.",
            "mx_host_used": "mx.catchall.com",
            "details": {}
        }
        res = verification_service.verify_email("anyuser@github.com")
        assert res.status == "RISKY"
        assert res.checks.catch_all.display_value == "YES"

def test_case_8_smtp_blocking_provider():
    # Mock SMTP service returning BLOCKED (port 25 firewall)
    with patch("app.services.verification_service.smtp_service.verify_mailbox_smtp") as mock_smtp:
        mock_smtp.return_value = {
            "attempted": True,
            "connected": False,
            "smtp_status": "BLOCKED",
            "mailbox_status": "UNCONFIRMED",
            "is_catch_all": False,
            "server_code": None,
            "server_message": "Port 25 outbound network restriction.",
            "mx_host_used": "mx.google.com",
            "details": {}
        }
        res = verification_service.verify_email("user@gmail.com")
        assert res.status == "UNKNOWN" # Must NOT be INVALID
        assert res.notification_sent is False

def test_case_9_timeout_case():
    # Mock DNS service returning timeout
    with patch("app.services.verification_service.dns_service.check_domain_dns") as mock_dns:
        mock_dns.return_value = {
            "domain": "timeoutdomain.com",
            "is_resolvable": False,
            "has_mx": False,
            "mx_records": [],
            "a_records": [],
            "error": "DNS query timed out",
            "is_timeout": True
        }
        res = verification_service.verify_email("user@timeoutdomain.com")
        assert res.status == "UNKNOWN" # Timeout must lead to UNKNOWN, not INVALID
        assert "timed out" in res.reason.lower()

def test_case_10_multiple_email_batch():
    batch_payload = {
        "emails": [
            "valid.user@gmail.com",
            "invalid-email-format",
            "user@nonexistent-domain-xyz-982138.com",
            "test@mailinator.com"
        ]
    }
    response = client.post("/api/v1/verify/batch", json=batch_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 4
    assert len(data["results"]) == 4
    assert data["valid_count"] + data["invalid_count"] + data["risky_count"] + data["unknown_count"] == 4

def test_case_11_invalid_characters_and_double_at():
    res1 = verification_service.verify_email("user@@gmail.com")
    assert res1.status == "INVALID"
    assert res1.checks.syntax.passed is False

    res2 = verification_service.verify_email("user name@gmail.com")
    assert res2.status == "INVALID"
    assert res2.checks.syntax.passed is False

def test_case_12_empty_input():
    res = verification_service.verify_email("")
    assert res.status == "INVALID"
    assert res.checks.syntax.passed is False

def test_case_13_duplicate_emails_in_batch():
    batch_payload = {
        "emails": [
            "john.doe@gmail.com",
            "john.doe@gmail.com"
        ]
    }
    response = client.post("/api/v1/verify/batch", json=batch_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["results"]) == 2
    # Ensure individual failures do not crash remaining verifications

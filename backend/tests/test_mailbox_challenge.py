import pytest
from unittest.mock import patch, MagicMock
from app.services.mailbox_challenge_service import mailbox_challenge_service
from app.services.verification_service import verification_service
from app.core.config import settings
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_mailbox_challenge_unconfigured_smtp_error():
    """When SMTP_HOST is not configured, the system must return a clear error and not claim code sent."""
    test_email = "unconfigured_smtp@example.com"
    with patch.object(settings, "SMTP_HOST", ""):
        res = client.post("/api/v1/mailbox/send-code", json={"email": test_email})
        assert res.status_code == 503
        assert "SMTP" in res.json()["detail"]

def test_mailbox_challenge_flow_with_smtp():
    """Tests the complete end-to-end SMTP code delivery and verification lifecycle."""
    test_email = "smtp_delivery_test@example.com"

    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__.return_value = mock_smtp_instance

    mock_dns = {
        "domain": "example.com",
        "is_resolvable": True,
        "has_mx": True,
        "mx_records": [{"priority": 10, "host": "mail.example.com"}],
        "a_records": ["93.184.215.14"],
        "error": None,
        "is_timeout": False,
    }

    with patch.object(settings, "SMTP_HOST", "smtp.mailgun.org"), \
         patch.object(settings, "SMTP_USERNAME", "postmaster@mailgun.org"), \
         patch.object(settings, "SMTP_PASSWORD", "testpass"), \
         patch("app.services.verification_service.dns_service.check_domain_dns", return_value=mock_dns), \
         patch("app.services.mailbox_challenge_service.smtplib.SMTP", return_value=mock_smtp_instance) as mock_smtp_cls:

        # Step 1: Send verification code
        send_res = client.post("/api/v1/mailbox/send-code", json={"email": test_email})
        assert send_res.status_code == 200
        send_data = send_res.json()
        assert send_data["success"] is True
        assert "Verification code sent" in send_data["message"]
        assert "code" not in send_data or send_data.get("code") is None

        # Verify SMTP interaction occurred
        assert mock_smtp_cls.called
        assert mock_smtp_instance.starttls.called
        assert mock_smtp_instance.login.called
        assert mock_smtp_instance.sendmail.called

        # Extract the sent email message string to get the generated code
        sendmail_args = mock_smtp_instance.sendmail.call_args[0]
        raw_msg = sendmail_args[2]
        assert "Verify your email address - MailScope" in raw_msg

        # Extract code from challenge internal state
        challenge = mailbox_challenge_service._challenges[test_email]
        salt = challenge["salt"]

        # Step 2: Test invalid code
        bad_res = client.post("/api/v1/mailbox/verify-code", json={"email": test_email, "code": "000000"})
        assert bad_res.status_code == 400
        assert "Invalid verification code" in bad_res.json()["detail"]

        # Find the correct code from 100000..999999 by computing test match
        correct_code = None
        for i in range(100000, 1000000):
            cand = str(i)
            if mailbox_challenge_service._hash_code(salt, cand) == challenge["code_hash"]:
                correct_code = cand
                break
        assert correct_code is not None

        # Step 3: Test valid code confirmation
        good_res = client.post("/api/v1/mailbox/verify-code", json={"email": test_email, "code": correct_code})
        assert good_res.status_code == 200
        good_data = good_res.json()
        assert good_data["success"] is True
        assert "verified successfully" in good_data["message"].lower()

        # Check that result is VALID with 100/100 score
        v_res = good_data["verification_result"]
        assert v_res["status"] == "VALID"
        assert v_res["score"] == 100
        assert v_res["checks"]["mailbox"]["display_value"] == "CONFIRMED"
        assert "✓ Mailbox verified" in v_res["checks"]["mailbox"]["message"]

def test_mailbox_challenge_cooldown():
    test_email = "cooldown_test_smtp@example.com"
    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__.return_value = mock_smtp_instance

    with patch.object(settings, "SMTP_HOST", "smtp.gmail.com"), \
         patch("smtplib.SMTP", return_value=mock_smtp_instance):

        # First request
        res1 = client.post("/api/v1/mailbox/send-code", json={"email": test_email})
        assert res1.status_code == 200

        # Second immediate request hits cooldown
        res2 = client.post("/api/v1/mailbox/send-code", json={"email": test_email})
        assert res2.status_code == 429
        assert "wait" in res2.json()["detail"].lower()

import pytest
from app.services.verification_service import verification_service

def test_score_calculation_for_invalid():
    res = verification_service.verify_email("invalid@@@syntax.com")
    assert res.score == 0
    assert res.status == "INVALID"
    assert res.checks.syntax.display_value == "FAIL"
    assert res.notification_sent is False

def test_status_for_disposable():
    # mailinator.com is disposable
    res = verification_service.verify_email("testuser@mailinator.com")
    assert res.checks.disposable.passed is False
    assert res.status == "RISKY"
    assert res.checks.disposable.display_value == "YES"
    assert res.notification_sent is False

def test_status_for_role_based():
    # info@gmail.com has valid domain & MX, but role-based local part
    res = verification_service.verify_email("info@gmail.com")
    assert res.checks.role_based.passed is False
    assert res.status in ["RISKY", "INVALID"]
    assert res.checks.role_based.display_value == "YES"
    assert res.notification_sent is False

def test_status_for_nonexistent_domain():
    res = verification_service.verify_email("user@nonexistent-domain-xyz-982138.com")
    assert res.status == "INVALID"
    assert res.score == 0
    assert res.checks.dns.display_value == "FAIL"
    assert res.notification_sent is False

def test_status_for_active_domain():
    res = verification_service.verify_email("unverified_user@gmail.com")
    assert res.status in ["VALID", "UNKNOWN", "INVALID"]
    assert res.checks.syntax.display_value == "PASS"
    assert res.checks.domain.display_value == "PASS"
    assert res.checks.dns.display_value == "PASS"
    assert res.checks.mx.display_value == "PASS"
    assert res.notification_sent is False

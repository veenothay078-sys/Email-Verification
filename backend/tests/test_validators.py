import pytest
from app.services.verification_service import verification_service
from app.data.disposable_domains import is_disposable_domain
from app.data.role_prefixes import is_role_based_local_part, is_free_email_domain

def test_syntax_validation():
    # Valid syntax
    res1 = verification_service.verify_email("test.user@example.com")
    assert res1.checks.syntax.passed is True
    assert res1.domain == "example.com"

    # Invalid syntax - missing @
    res2 = verification_service.verify_email("invalidemail.com")
    assert res2.checks.syntax.passed is False
    assert res2.status == "INVALID"

    # Invalid syntax - spaces
    res3 = verification_service.verify_email("invalid email@test.com")
    assert res3.checks.syntax.passed is False
    assert res3.status == "INVALID"

    # Empty email
    res4 = verification_service.verify_email("")
    assert res4.checks.syntax.passed is False
    assert res4.status == "INVALID"

def test_disposable_domain_detection():
    assert is_disposable_domain("mailinator.com") is True
    assert is_disposable_domain("tempmail.com") is True
    assert is_disposable_domain("sub.mailinator.com") is True
    assert is_disposable_domain("10minutemail.com") is True
    assert is_disposable_domain("gmail.com") is False
    assert is_disposable_domain("microsoft.com") is False

def test_role_based_detection():
    assert is_role_based_local_part("support") is True
    assert is_role_based_local_part("admin") is True
    assert is_role_based_local_part("sales") is True
    assert is_role_based_local_part("noreply") is True
    assert is_role_based_local_part("info") is True
    assert is_role_based_local_part("billing") is True
    assert is_role_based_local_part("support-team") is True
    assert is_role_based_local_part("john.doe") is False
    assert is_role_based_local_part("sarah_connor") is False

def test_free_provider_detection():
    assert is_free_email_domain("gmail.com") is True
    assert is_free_email_domain("outlook.com") is True
    assert is_free_email_domain("yahoo.com") is True
    assert is_free_email_domain("company.org") is False

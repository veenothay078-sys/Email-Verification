"""
Role-based email prefix definitions and free email providers database.
"""

ROLE_PREFIXES = {
    "admin",
    "administrator",
    "support",
    "help",
    "info",
    "sales",
    "contact",
    "contactus",
    "billing",
    "invoice",
    "payments",
    "accounting",
    "careers",
    "jobs",
    "hr",
    "recruitment",
    "marketing",
    "media",
    "press",
    "pr",
    "security",
    "abuse",
    "postmaster",
    "hostmaster",
    "webmaster",
    "noreply",
    "no-reply",
    "donotreply",
    "system",
    "mailer-daemon",
    "office",
    "team",
    "general",
    "inquiries",
    "enquiry",
    "legal",
    "compliance",
    "privacy",
    "dev",
    "ops",
    "engineering",
    "feedback",
}

FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "ymail.com",
    "rocketmail.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "msn.com",
    "icloud.com",
    "me.com",
    "mac.com",
    "aol.com",
    "protonmail.com",
    "proton.me",
    "zoho.com",
    "gmx.com",
    "gmx.net",
    "mail.com",
    "tutanota.com",
    "tuta.io",
    "fastmail.com",
    "hushmail.com",
}

def is_role_based_local_part(local_part: str) -> bool:
    """Check if the local part of an email address matches common role prefixes."""
    if not local_part:
        return False
    lp = local_part.lower().strip()
    # Normalize separators like dot, underscore, hyphen
    clean_lp = lp.replace(".", "").replace("-", "").replace("_", "")
    
    if lp in ROLE_PREFIXES or clean_lp in ROLE_PREFIXES:
        return True
        
    # Also check compound prefixes like support-team or info_us
    for prefix in ROLE_PREFIXES:
        if lp.startswith(prefix + "-") or lp.startswith(prefix + "_") or lp.startswith(prefix + "."):
            return True
            
    return False

def is_free_email_domain(domain: str) -> bool:
    """Check if domain is a common free webmail provider."""
    if not domain:
        return False
    return domain.lower().strip() in FREE_EMAIL_DOMAINS

"""
Curated open-source list of disposable/temporary email provider domains.
Sources include standard open-source datasets (e.g., disposable-email-domains community lists).
"""

DISPOSABLE_DOMAINS = {
    # Popular disposable email domains
    "mailinator.com",
    "tempmail.com",
    "temp-mail.org",
    "10minutemail.com",
    "10minutemail.net",
    "guerrillamail.com",
    "guerrillamail.net",
    "guerrillamail.org",
    "guerrillamail.biz",
    "grr.la",
    "sharklasers.com",
    "yopmail.com",
    "yopmail.fr",
    "yopmail.net",
    "throwawaymail.com",
    "trashmail.com",
    "trashmail.net",
    "trashmail.org",
    "getairmail.com",
    "dispostable.com",
    "maildrop.cc",
    "crazymailing.com",
    "inboxkitten.com",
    "fakeinbox.com",
    "mytemp.email",
    "burnermail.io",
    "mohmal.com",
    "dropmail.me",
    "fakemailgenerator.com",
    "emailondeck.com",
    "tempail.com",
    "throwawayemailaddress.com",
    "generator.email",
    "nada.ltd",
    "getnada.com",
    "inboxbear.com",
    "harakirimail.com",
    "trashinbox.com",
    "mailnesia.com",
    "tmail.ws",
    "tmpmail.net",
    "tmpmail.org",
    "boun.cr",
    "jetable.org",
    "tempinbox.com",
    "spambox.us",
    "0-mail.com",
    "10mail.org",
    "20minutemail.com",
    "armyspy.com",
    "cuvox.de",
    "dayrep.com",
    "einrot.com",
    "fleckens.hu",
    "gustr.com",
    "jourrapide.com",
    "rhyta.com",
    "superrito.com",
    "teleworm.us",
    "trbvm.com",
}

def is_disposable_domain(domain: str) -> bool:
    """Check if domain or parent domain matches known disposable list."""
    if not domain:
        return False
    d = domain.lower().strip()
    if d in DISPOSABLE_DOMAINS:
        return True
    # Check subdomain match (e.g. sub.mailinator.com)
    parts = d.split(".")
    if len(parts) > 2:
        parent = ".".join(parts[-2:])
        if parent in DISPOSABLE_DOMAINS:
            return True
    return False

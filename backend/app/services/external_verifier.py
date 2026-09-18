import urllib.request
import json
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger("mailscope.external_verifier")

class ExternalVerificationAdapter:
    """
    Adapter for querying an authorized external email verification service/API
    when configured via environment variables (EXTERNAL_VERIFIER_ENABLED=true).
    Does NOT execute unless explicitly configured.
    """
    def __init__(self):
        self.enabled = settings.EXTERNAL_VERIFIER_ENABLED
        self.url = settings.EXTERNAL_VERIFIER_URL
        self.api_key = settings.EXTERNAL_VERIFIER_API_KEY

    def verify_email_external(self, email: str) -> Optional[Dict[str, Any]]:
        if not self.enabled or not self.url or not self.api_key:
            return None

        try:
            req_url = f"{self.url}?email={email}&api_key={self.api_key}"
            req = urllib.request.Request(
                req_url,
                headers={"User-Agent": "MailScope/1.0", "Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode())
                    return {
                        "is_valid": data.get("is_valid"),
                        "evidence": data.get("evidence", "CONFIRMED_EXISTS" if data.get("is_valid") else "CONFIRMED_REJECTED"),
                        "raw": data
                    }
        except Exception as e:
            logger.warning(f"External verification adapter error: {e}")
        
        return None

external_verifier = ExternalVerificationAdapter()

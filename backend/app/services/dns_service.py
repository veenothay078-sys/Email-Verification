import dns.resolver
import dns.exception
from typing import Dict, List, Any, Optional
from app.core.config import settings

class DNSService:
    def __init__(self, timeout: float = settings.DNS_TIMEOUT_SECONDS, lifetime: float = settings.DNS_LIFETIME_SECONDS):
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = timeout
        self.resolver.lifetime = lifetime
        # Use system DNS servers or public DNS fallback if needed
        self.resolver.nameservers = ['8.8.8.8', '1.1.1.1']

    def check_domain_dns(self, domain: str) -> Dict[str, Any]:
        """
        Performs comprehensive DNS inspection:
        - A/AAAA record lookup for domain resolvability
        - MX record lookup with priority and hostnames
        - Timeout and exception handling
        """
        result = {
            "domain": domain,
            "is_resolvable": False,
            "has_mx": False,
            "mx_records": [],
            "a_records": [],
            "error": None,
            "is_timeout": False,
        }

        if not domain:
            result["error"] = "Empty domain"
            return result

        # 1. Resolve A / AAAA records to verify domain existence
        try:
            a_answers = self.resolver.resolve(domain, 'A')
            result["a_records"] = [str(rdata) for rdata in a_answers]
            result["is_resolvable"] = True
        except dns.resolver.NXDOMAIN:
            result["is_resolvable"] = False
            result["error"] = "Domain does not exist (NXDOMAIN)"
            return result
        except dns.resolver.NoAnswer:
            # Try AAAA (IPv6)
            try:
                aaaa_answers = self.resolver.resolve(domain, 'AAAA')
                result["a_records"] = [str(rdata) for rdata in aaaa_answers]
                result["is_resolvable"] = True
            except Exception:
                result["is_resolvable"] = False
        except dns.exception.Timeout:
            result["is_timeout"] = True
            result["error"] = "DNS query timed out"
            return result
        except Exception as e:
            result["error"] = str(e)

        # 2. Resolve MX records
        try:
            mx_answers = self.resolver.resolve(domain, 'MX')
            mx_list = []
            for rdata in mx_answers:
                mx_list.append({
                    "priority": rdata.preference,
                    "host": str(rdata.exchange).rstrip('.'),
                })
            # Sort by priority (lowest preference number first)
            mx_list.sort(key=lambda x: x["priority"])
            result["mx_records"] = mx_list
            result["has_mx"] = len(mx_list) > 0
            if result["has_mx"]:
                result["is_resolvable"] = True
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            result["has_mx"] = False
            # If domain has A records but no MX, RFC 5321 allows fallback to A record, but MX is preferred
        except dns.exception.Timeout:
            result["is_timeout"] = True
            if not result["error"]:
                result["error"] = "MX DNS query timed out"
        except Exception as e:
            if not result["error"]:
                result["error"] = str(e)

        return result

dns_service = DNSService()

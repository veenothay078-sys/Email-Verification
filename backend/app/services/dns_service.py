import time
import copy
import threading
import dns.resolver
import dns.exception
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from app.core.config import settings

class DNSService:
    def __init__(self, timeout: float = settings.DNS_TIMEOUT_SECONDS, lifetime: float = settings.DNS_LIFETIME_SECONDS):
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = timeout
        self.resolver.lifetime = lifetime
        self.resolver.nameservers = ['8.8.8.8', '1.1.1.1']
        
        # Thread-safe in-memory cache: domain -> (timestamp, result_dict)
        self._cache: Dict[str, Any] = {}
        self._cache_lock = threading.Lock()

    def _resolve_a_records(self, domain: str) -> Dict[str, Any]:
        """Helper to resolve A / AAAA records."""
        a_records = []
        is_resolvable = False
        error = None
        is_timeout = False

        try:
            a_answers = self.resolver.resolve(domain, 'A')
            a_records = [str(rdata) for rdata in a_answers]
            is_resolvable = True
        except dns.resolver.NXDOMAIN:
            is_resolvable = False
            error = "Domain does not exist (NXDOMAIN)"
        except dns.resolver.NoAnswer:
            try:
                aaaa_answers = self.resolver.resolve(domain, 'AAAA')
                a_records = [str(rdata) for rdata in aaaa_answers]
                is_resolvable = True
            except Exception:
                is_resolvable = False
        except dns.exception.Timeout:
            is_timeout = True
            error = "DNS A query timed out"
        except Exception as e:
            error = str(e)

        return {
            "is_resolvable": is_resolvable,
            "a_records": a_records,
            "error": error,
            "is_timeout": is_timeout
        }

    def _resolve_mx_records(self, domain: str) -> Dict[str, Any]:
        """Helper to resolve MX records."""
        mx_list = []
        has_mx = False
        error = None
        is_timeout = False

        try:
            mx_answers = self.resolver.resolve(domain, 'MX')
            for rdata in mx_answers:
                mx_list.append({
                    "priority": rdata.preference,
                    "host": str(rdata.exchange).rstrip('.'),
                })
            mx_list.sort(key=lambda x: x["priority"])
            has_mx = len(mx_list) > 0
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            has_mx = False
        except dns.exception.Timeout:
            is_timeout = True
            error = "MX DNS query timed out"
        except Exception as e:
            error = str(e)

        return {
            "has_mx": has_mx,
            "mx_records": mx_list,
            "error": error,
            "is_timeout": is_timeout
        }

    def check_domain_dns(self, domain: str) -> Dict[str, Any]:
        """
        Performs optimized DNS inspection with in-memory TTL caching
        and parallel A/MX record lookups.
        """
        if not domain:
            return {
                "domain": "",
                "is_resolvable": False,
                "has_mx": False,
                "mx_records": [],
                "a_records": [],
                "error": "Empty domain",
                "is_timeout": False,
                "cached": False
            }

        domain_key = domain.strip().lower()
        now = time.time()
        ttl = getattr(settings, "DNS_CACHE_TTL_SECONDS", 300)

        # 1. Check TTL Cache
        with self._cache_lock:
            if domain_key in self._cache:
                cached_time, cached_res = self._cache[domain_key]
                if now - cached_time < ttl:
                    res_copy = copy.deepcopy(cached_res)
                    res_copy["cached"] = True
                    return res_copy

        # 2. Parallel Pre-checks (A & MX lookups executed concurrently)
        with ThreadPoolExecutor(max_workers=2) as executor:
            a_future = executor.submit(self._resolve_a_records, domain_key)
            mx_future = executor.submit(self._resolve_mx_records, domain_key)

            a_res = a_future.result()
            mx_res = mx_future.result()

        is_resolvable = a_res["is_resolvable"] or mx_res["has_mx"]
        has_mx = mx_res["has_mx"]
        error = a_res["error"] or mx_res["error"]
        is_timeout = a_res["is_timeout"] or mx_res["is_timeout"]

        result = {
            "domain": domain_key,
            "is_resolvable": is_resolvable,
            "has_mx": has_mx,
            "mx_records": mx_res["mx_records"],
            "a_records": a_res["a_records"],
            "error": error,
            "is_timeout": is_timeout,
            "cached": False
        }

        # 3. Store in TTL Cache
        with self._cache_lock:
            self._cache[domain_key] = (now, result)

        return result

    def clear_cache(self):
        """Clears in-memory DNS cache."""
        with self._cache_lock:
            self._cache.clear()

dns_service = DNSService()

import urllib.request
import json
import time

def run_test_suite():
    tests = [
        ("Known Gmail", "veenothay078@gmail.com"),
        ("Random Gmail", "randomxyz987654321987@gmail.com"),
        ("Valid-looking Outlook", "sarah.connor@outlook.com"),
        ("Random Outlook", "random-outlook-user-999999@outlook.com"),
        ("Malformed Email", "john@@gmail..com"),
        ("Nonexistent Domain", "user@nonexistent-domain-xyz-99999.com"),
        ("Disposable Domain", "test@mailinator.com"),
        ("Role Alias", "info@gmail.com"),
    ]

    print("======================================================================")
    print("MAILSCOPE VERIFICATION ENGINE — EVIDENCE & CAPABILITY MODEL MATRIX")
    print("======================================================================")

    for label, email in tests:
        t0 = time.time()
        try:
            req = urllib.request.Request(
                "http://localhost:8000/api/v1/verify",
                data=json.dumps({"email": email}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            res = json.loads(urllib.request.urlopen(req).read().decode())
            duration = round(time.time() - t0, 2)
            print(f"LABEL:                    {label}")
            print(f"EMAIL:                    {res.get('email')}")
            print(f"STATUS:                   {res.get('status')}")
            print(f"MAILBOX EXISTENCE:        {res.get('mailbox_existence')}")
            print(f"VERIFICATION CAPABILITY:  {res.get('verification_capability')}")
            print(f"MAILBOX EVIDENCE:         {res.get('mailbox_evidence')}")
            print(f"CONFIDENCE LEVEL:         {res.get('confidence_level')} ({res.get('score')}/100)")
            print(f"NOTIFICATION SENT:        {res.get('notification_sent')}")
            print(f"REASON:                   {res.get('reason')}")
            print(f"CHECKS:")
            print(f"  - SYNTAX                : {res['syntax_valid']}")
            print(f"  - DOMAIN                : {res['domain_exists']}")
            print(f"  - DNS RESOLVED          : {res['dns_resolved']}")
            print(f"  - MX FOUND              : {res['mx_found']} ({res.get('mx_host')})")
            print(f"  - SMTP CONNECTED        : {res['smtp_connection']}")
            print(f"  - CATCH_ALL DETECTED    : {res['catch_all_detected']}")
            print(f"  - DISPOSABLE DETECTED   : {res['disposable_detected']}")
            print(f"  - RISK SIGNALS          : {res['risk_signals']}")
            print(f"DURATION:                 {duration}s")
            print("----------------------------------------------------------------------")
        except Exception as e:
            print(f"LABEL: {label} ({email}) -> ERROR: {e}")
            print("----------------------------------------------------------------------")

if __name__ == "__main__":
    run_test_suite()

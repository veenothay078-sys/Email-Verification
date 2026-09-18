import httpx
import json

client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=30.0)

test_cases = [
    "john@@gmail.com",
    "user@nonexistent-domain-xyz-982138.com",
    "test@mailinator.com",
    "info@gmail.com",
    "alex.smith@gmail.com",
]

print("=" * 70)
print("MAILSCOPE NON-DELIVERY TECHNICAL VERIFICATION MATRIX TEST")
print("=" * 70)

for email in test_cases:
    try:
        res = client.post("/api/v1/verify", json={"email": email})
        data = res.json()
        print(f"EMAIL:              {data.get('email')}")
        print(f"STATUS:             {data.get('status')}")
        print(f"CONFIDENCE LEVEL:   {data.get('confidence_level')} ({data.get('confidence')}/100)")
        print(f"VERIFICATION METHOD:{data.get('verification_method')}")
        print(f"NOTIFICATION SENT:  {'YES' if data.get('notification_sent') else 'NO'}")
        print(f"REASON:             {data.get('reason')}")
        print(f"MESSAGE:            {data.get('message')}")
        print("CHECKS:")
        for k, v in data.get("checks", {}).items():
            if isinstance(v, dict):
                disp = v.get("display_value", v.get("status", ""))
                print(f"  - {k.upper():<14}: {disp}")
        print("-" * 70)
    except Exception as exc:
        print(f"Error testing {email}: {exc}")

print("\nBATCH VERIFICATION TEST (CONCURRENT EXECUTOR):")
try:
    batch_res = client.post("/api/v1/verify/batch", json={"emails": test_cases})
    batch_data = batch_res.json()
    print(f"Total: {batch_data.get('total')}, Valid: {batch_data.get('valid_count')}, Invalid: {batch_data.get('invalid_count')}, Risky: {batch_data.get('risky_count')}, Unknown: {batch_data.get('unknown_count')}")
    print(f"Average Score: {batch_data.get('average_score')}")
except Exception as exc:
    print(f"Error in batch test: {exc}")
print("=" * 70)

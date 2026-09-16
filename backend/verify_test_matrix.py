import httpx
import json

client = httpx.Client(base_url="http://127.0.0.1:8001", timeout=10.0)

test_cases = [
    "john@@gmail.com",
    "user@nonexistent-domain-xyz-982138.com",
    "test@mailinator.com",
    "info@gmail.com",
    "abcxyz123@gmail.com",
]

print("=" * 65)
for email in test_cases:
    res = client.post("/api/v1/verify", json={"email": email})
    data = res.json()
    print(f"EMAIL:       {data['email']}")
    print(f"STATUS:      {data['status']}")
    print(f"CONFIDENCE:  {data['confidence']}/100")
    print(f"REASON:      {data['reason']}")
    print(f"MESSAGE:     {data['message']}")
    print("CHECKS:")
    for k, v in data["checks"].items():
        if isinstance(v, dict):
            disp = v.get("display_value", v.get("status", ""))
            print(f"  - {k.upper():<14}: {disp}")
    print("-" * 65)

# Test Mailbox Verification OTP Flow
print("\n=================================================================")
print("MAILBOX VERIFICATION CODE CONFIRMATION FLOW TEST:")
target_test = "abcxyz123@gmail.com"
res = client.post("/api/v1/mailbox/send-code", json={"email": target_test})
print(f"1. Send Code Status: {res.status_code}, Response: {res.json()}")
if res.status_code == 200:
    print("Code sent successfully via outbound SMTP.")
elif res.status_code == 503:
    print("Verified real-outbound requirement: 503 returned when SMTP credentials not provided in .env.")
print("=================================================================")

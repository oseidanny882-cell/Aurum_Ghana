"""
Test script: admin email-OTP login security checks.
Run: python scripts/test_otp_security.py
(Codes tested here are already-consumed/invalid, so this is safe to re-run.)
"""
import json, urllib.request, urllib.error

def test(code):
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/v1/auth/mfa-email-verify",
        data=json.dumps({"email": "richmondayeh6@icloud.com", "code": code}).encode(),
        headers={"Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req)
        print(f"code {code} -> {r.status} (unexpected)")
    except urllib.error.HTTPError as e:
        print(f"code {code} -> {e.code} (rejected OK)")

test("867689")   # reuse of already-consumed code
test("999999")   # never-valid code

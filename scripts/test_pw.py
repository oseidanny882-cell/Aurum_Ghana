"""Test the change-password endpoint directly to capture the exact 400."""
import urllib.request, json, sys
sys.path.insert(0, r"c:/Users/Codewithme/jewelry-gh")

login_payload = json.dumps({
    "email": "admin@aurum-ghana.local",
    "password": "Admin12345!"
}).encode()
try:
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/v1/auth/login",
        data=login_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    r = urllib.request.urlopen(req, timeout=10)
    body = json.loads(r.read())
    token = body.get("access_token")
    print("Login OK, got token")
except urllib.error.HTTPError as e:
    print(f"Login failed: HTTP {e.code} {e.read().decode()[:300]}")
    sys.exit(1)
except Exception as e:
    print(f"Login FAILED: {e}")
    sys.exit(1)

def try_change(new_pw, label):
    print(f"\n{label}: '{new_pw}'")
    pw_payload = json.dumps({
        "current_password": "Admin12345!",
        "new_password": new_pw
    }).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/v1/user/change-password",
        data=pw_payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST"
    )
    try:
        r = urllib.request.urlopen(req, timeout=15)
        print(f"  OK: {r.read().decode()[:200]}")
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.read().decode()[:300]}")

try_change("Short1Aa", "Test 1 - 8 chars (was old minimum)")
try_change("Password1234", "Test 2 - 12 chars common")
try_change("MyStr0ng-Pass!2026", "Test 3 - 14 chars strong")
try_change("OnlyLettersHere", "Test 4 - no number")

"""Test the change-password endpoint directly to capture the exact 400."""
import urllib.request, json, sys
sys.path.insert(0, r"c:/Users/Codewithme/jewelry-gh")

# Login first to get a token
login_payload = json.dumps({
    "email": "admin@aurum-ghana.local",
    "password": "Admin@12345"
}).encode()
try:
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/v1/auth/login",
        data=login_payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    r = urllib.request.urlopen(req, timeout=10)
    body = json.loads(r.read())
    token = body.get("access_token")
    print("Login OK, got token")
except urllib.error.HTTPError as e:
    print(f"Login failed: HTTP {e.code} {e.read().decode()[:300]}")
    sys.exit(1)
except Exception as e:
    print(f"Login FAILED: {e}")
    sys.exit(1)

# Now try change-password with a short password (10 chars < 12 min)
print("\nTest 1: short new password (10 chars)")
pw_payload = json.dumps({
    "current_password": "Admin@12345",
    "new_password": "Short1Aa"
}).encode()
try:
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/v1/user/change-password",
        data=pw_payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        method="POST"
    )
    r = urllib.request.urlopen(req, timeout=10)
    print("OK:", r.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()[:400]}")

# Test 2: too short = should give weak_password
print("\nTest 2: 14-char but HIBP check")
pw_payload = json.dumps({
    "current_password": "Admin@12345",
    "new_password": "Password1234!"   # 13 chars, possibly breached
}).encode()
try:
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/v1/user/change-password",
        data=pw_payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST"
    )
    r = urllib.request.urlopen(req, timeout=15)
    print("OK:", r.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()[:400]}")

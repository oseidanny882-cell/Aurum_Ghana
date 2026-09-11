"""Quick test: verify both servers are up and auth is reachable."""
import urllib.request, json, sys

# Test 1: backend health
try:
    r = urllib.request.urlopen("http://127.0.0.1:5000/health", timeout=5)
    data = json.loads(r.read())
    print(f"Backend health: {data}")
except Exception as e:
    print(f"Backend health FAILED: {e}")
    sys.exit(1)

# Test 2: frontend
try:
    r = urllib.request.urlopen("http://127.0.0.1:8080/index.html", timeout=5)
    body = r.read()
    print(f"Frontend /index.html: HTTP {r.status}, {len(body)} bytes")
except Exception as e:
    print(f"Frontend FAILED: {e}")
    sys.exit(1)

# Test 3: register endpoint (should reach the route, might fail validation)
payload = json.dumps({
    "email": "test@example.com",
    "password": "Test1234abcd",
    "name": "Test User",
    "phone": "0241234567"
}).encode()
try:
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/v1/auth/register",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    r = urllib.request.urlopen(req, timeout=10)
    print(f"Register: HTTP {r.status}, {r.read().decode()[:300]}")
except urllib.error.HTTPError as e:
    body = e.read().decode()[:300]
    print(f"Register: HTTP {e.code} (expected if email exists), body: {body}")
except Exception as e:
    print(f"Register FAILED: {e}")

print("\nBoth servers are running!")
print("  Backend: http://localhost:5000")
print("  Frontend: http://localhost:8080")

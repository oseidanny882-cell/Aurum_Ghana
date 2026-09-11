"""Debug auth refresh token flow."""
import requests, jwt

BASE = 'http://127.0.0.1:5000/api/v1'

# Login
r = requests.post(f'{BASE}/auth/login', json={'email': 'yaw@example.com', 'password': 'TestPass123!'})
data = r.json()
access = data['access_token']
refresh = data.get('refresh_token')
print(f'access_token present: {bool(access)}')
print(f'refresh_token present: {bool(refresh)}')

if refresh:
    # Decode JWT payload without verification
    try:
        parts = refresh.split('.')
        payload = parts[1] + '=='
        import base64, json as json_mod
        decoded_bytes = base64.urlsafe_b64decode(payload)
        payload_dict = json_mod.loads(decoded_bytes)
        print(f'Refresh token type claim: {payload_dict.get("type")}')
        print(f'Refresh token exp: {payload_dict.get("exp")}')
    except Exception as e:
        print(f'Refresh decode error: {e}')

    # Try refresh endpoint
    r2 = requests.post(
        f'{BASE}/auth/refresh',
        json={'refresh_token': refresh},
        headers={'Content-Type': 'application/json'}
    )
    print(f'Refresh status: {r2.status_code} - {r2.text[:200]}')
else:
    print('No refresh token returned by login!')
    print(f'Login response keys: {list(data.keys())}')

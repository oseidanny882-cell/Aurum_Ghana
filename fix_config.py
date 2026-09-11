import sys

path = 'backend/config.py'
lines = open(path).readlines()
for i, line in enumerate(lines):
    if 'JWT_COOKIE_CSRF_PROTECT' in line:
        lines[i] = '    JWT_COOKIE_CSRF_PROTECT = os.getenv("JWT_COOKIE_CSRF_PROTECT", "true").lower() in ("1", "true", "yes")\n'
        break

with open(path, 'w') as f:
    f.writelines(lines)

print('Fixed')

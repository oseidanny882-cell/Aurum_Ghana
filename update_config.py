import os
content = open("backend/config.py").read()
old = "JWT_CSRF_IN_COOKIES = False"
new = old + "\n    JWT_TOKEN_COOKIE = \"access_token_cookie\"\n    JWT_REFRESH_COOKIE = \"refresh_token_cookie\""
content = content.replace(old, new)
with open("backend/config.py", "w") as f:
    f.write(content)
print("Done")

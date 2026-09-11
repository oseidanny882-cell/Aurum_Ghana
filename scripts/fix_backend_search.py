import pathlib

p = pathlib.Path("c:/Users/Codewithme/jewelry-gh/backend/api/products.py")
t = p.read_text(encoding="utf-8")

old = '''    search = request.args.get("q")
    if search:'''

new = '''    # Accept both "q" (API convention) and "search" (user-friendly URL)
    search = request.args.get("q") or request.args.get("search")
    if search:'''

if old in t:
    t = t.replace(old, new)
    p.write_text(t, encoding="utf-8")
    print("SUCCESS: Backend now accepts both q and search params")
else:
    print("ERROR: old text not found")
    idx = t.find("search = request.args.get")
    if idx >= 0:
        print(repr(t[max(0,idx-100):idx+200]))

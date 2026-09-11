import pathlib

p = pathlib.Path("c:/Users/Codewithme/jewelry-gh/backend/api/products.py")
t = p.read_text(encoding="utf-8")

old_doc = "GET  /products          - List with filters (category, q, featured, is_new, is_best, page, per_page)"
new_doc = "GET  /products          - List with filters (category, q, featured, is_new, is_best, filter=new|best|sale, page, per_page)"

if old_doc in t:
    t = t.replace(old_doc, new_doc)
    p.write_text(t, encoding="utf-8")
    print("SUCCESS: Updated docstring")
else:
    print("ERROR: docstring not found")

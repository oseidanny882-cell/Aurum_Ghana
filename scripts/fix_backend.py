import pathlib

p = pathlib.Path("c:/Users/Codewithme/jewelry-gh/backend/api/products.py")
t = p.read_text(encoding="utf-8")

# Fix the duplicate lines from earlier insert
bad = '''    if request.args.get("filter") == "new":
    if request.args.get("filter") == "new":
        q = q.filter(Product.is_new.is_(True)).order_by(Product.created_at.desc())
    elif request.args.get("filter") == "best":
        q = q.filter(Product.is_best.is_(True)).order_by(Product.rating_avg.desc())
    elif request.args.get("filter") == "sale":
        q = q.filter(Product.discount_price.isnot(None), Product.discount_price > 0).order_by(Product.discount_price.asc())
        q = q.filter(Product.is_new.is_(True)).order_by(Product.created_at.desc())
    elif request.args.get("filter") == "best":
        q = q.filter(Product.is_best.is_(True)).order_by(Product.rating_avg.desc())'''

good = '''    if request.args.get("filter") == "new":
        q = q.filter(Product.is_new.is_(True)).order_by(Product.created_at.desc())
    elif request.args.get("filter") == "best":
        q = q.filter(Product.is_best.is_(True)).order_by(Product.rating_avg.desc())
    elif request.args.get("filter") == "sale":
        q = q.filter(Product.discount_price.isnot(None), Product.discount_price > 0).order_by(Product.discount_price.asc())'''

if bad in t:
    t = t.replace(bad, good)
    p.write_text(t, encoding="utf-8")
    print("SUCCESS: Fixed duplicate filter lines")
else:
    print("ERROR: bad text not found")
    # Show what's actually there
    idx = t.find('request.args.get("filter")')
    print(repr(t[max(0,idx-50):idx+800]))

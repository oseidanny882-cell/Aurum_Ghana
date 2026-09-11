import pathlib

p = pathlib.Path("c:/Users/Codewithme/jewelry-gh/frontend/scripts.js")
t = p.read_text(encoding="utf-8")

# Fix the broken global init - lines 536-540 contain leaked code from initCategoryPage
bad = '''        if (page === "product")   await initProductPage();

        var g = document.getElementById("product-grid"), cnt = document.getElementById("product-count"), sort = document.getElementById("sort-select");
        var filterBtns = document.querySelectorAll(".filter-bar .filter-btn");

        if (!g) return;
        var filterBtns = document.querySelectorAll(".filter-bar .filter-btn");

        if (page === "cart")      initCartPage();'''

good = '''        if (page === "product")   await initProductPage();

        if (page === "cart")      initCartPage();'''

if bad in t:
    t = t.replace(bad, good)
    p.write_text(t, encoding="utf-8")
    print("SUCCESS: Fixed global init - removed leaked code")
else:
    print("ERROR: bad text not found")
    # Show what's there
    idx = t.find('if (page === "product")   await initProductPage();')
    print(repr(t[idx:idx+500]))

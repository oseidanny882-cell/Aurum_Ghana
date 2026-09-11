import pathlib

p = pathlib.Path("c:/Users/Codewithme/jewelry-gh/frontend/scripts.js")
t = p.read_text(encoding="utf-8")

# Add filterBtns variable to initCategoryPage
old1 = "var g = document.getElementById(\"product-grid\"), cnt = document.getElementById(\"product-count\"), sort = document.getElementById(\"sort-select\");\n\n        if (!g) return;"

new1 = "var g = document.getElementById(\"product-grid\"), cnt = document.getElementById(\"product-count\"), sort = document.getElementById(\"sort-select\");\n        var filterBtns = document.querySelectorAll(\".filter-bar .filter-btn\");\n\n        if (!g) return;"

if old1 in t:
    t = t.replace(old1, new1)
    print("Step 1: SUCCESS - Added filterBtns variable")
else:
    print("Step 1: ERROR - old1 text not found")

# Add filter param reading
old2 = "if (u.get(\"search\")) { p.search = u.get(\"search\"); document.title = \"Search: \" + u.get(\"search\") + \" - Aurum Ghana\"; }\n\n            if (sort) p.sort = sort.value;"

new2 = "if (u.get(\"search\")) { p.search = u.get(\"search\"); document.title = \"Search: \" + u.get(\"search\") + \" - Aurum Ghana\"; }\n            if (u.get(\"filter\")) p.filter = u.get(\"filter\");\n\n            if (sort) p.sort = sort.value;"

if old2 in t:
    t = t.replace(old2, new2)
    print("Step 2: SUCCESS - Added filter param reading")
else:
    print("Step 2: ERROR - old2 text not found")

# Add filter button click handlers and popstate listener
old3 = "if (sort) sort.addEventListener(\"change\", load);\n\n        load();\n\n    }"

new3 = """if (filterBtns && filterBtns.length) {
            filterBtns.forEach(btn => {
                btn.addEventListener("click", () => {
                    var filter = btn.getAttribute("data-filter");
                    var u = new URLSearchParams(window.location.search);
                    if (filter) {
                        u.set("filter", filter);
                        u.delete("cat");
                    } else {
                        u.delete("filter");
                    }
                    var newQuery = u.toString();
                    var newUrl = window.location.pathname + (newQuery ? "?" + newQuery : "");
                    window.history.pushState({}, "", newUrl);
                    filterBtns.forEach(b => b.classList.remove("active"));
                    btn.classList.add("active");
                    load();
                });
            });
        }

        window.addEventListener("popstate", load);

        if (sort) sort.addEventListener("change", load);

        load();

    }"""

if old3 in t:
    t = t.replace(old3, new3)
    print("Step 3: SUCCESS - Added filter button handlers")
else:
    print("Step 3: ERROR - old3 text not found")

p.write_text(t, encoding="utf-8")
print("File saved")

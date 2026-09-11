import pathlib

p = pathlib.Path("c:/Users/Codewithme/jewelry-gh/frontend/scripts.js")
t = p.read_text(encoding="utf-8")

# Fix 1: initCategoryPage should read 'search' from URL (user-friendly URL)
# but send 'q' to the API (backend param name). Also persist search across filter changes.
old1 = '''            if (u.get("search")) { p.search = u.get("search"); document.title = "Search: " + u.get("search") + " - Aurum Ghana"; }
            if (u.get("filter")) p.filter = u.get("filter");'''

new1 = '''            if (u.get("search")) { p.q = u.get("search"); document.title = "Search: " + u.get("search") + " - Aurum Ghana"; }
            if (u.get("filter")) p.filter = u.get("filter");'''

# Fix 2: Filter button handler - preserve search param when switching filters
old2 = '''                btn.addEventListener("click", () => {
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
                });'''

new2 = '''                btn.addEventListener("click", () => {
                    var filter = btn.getAttribute("data-filter");
                    var u = new URLSearchParams(window.location.search);
                    if (filter) {
                        u.set("filter", filter);
                        u.delete("cat");
                    } else {
                        u.delete("filter");
                    }
                    // Preserve search param when switching filters
                    var searchVal = u.get("search");
                    var newQuery = u.toString();
                    var newUrl = window.location.pathname + (newQuery ? "?" + newQuery : "");
                    window.history.pushState({}, "", newUrl);
                    filterBtns.forEach(b => b.classList.remove("active"));
                    btn.classList.add("active");
                    load();
                });'''

# Fix 3: initCategoryPage - highlight the correct filter button based on URL on page load
# Also handle "All" button active state on page load
old3 = '''        if (filterBtns && filterBtns.length) {
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
                    // Preserve search param when switching filters
                    var searchVal = u.get("search");
                    var newQuery = u.toString();
                    var newUrl = window.location.pathname + (newQuery ? "?" + newQuery : "");
                    window.history.pushState({}, "", newUrl);
                    filterBtns.forEach(b => b.classList.remove("active"));
                    btn.classList.add("active");
                    load();
                });
            });
        }'''

new3 = '''        // Set active filter button based on current URL on page load
        if (filterBtns && filterBtns.length) {
            var loadUrl = new URLSearchParams(window.location.search);
            var currentFilter = loadUrl.get("filter") || "";
            filterBtns.forEach(btn => {
                if (btn.getAttribute("data-filter") === currentFilter) {
                    btn.classList.add("active");
                } else {
                    btn.classList.remove("active");
                }
            });
        }

        if (filterBtns && filterBtns.length) {
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
        }'''

changes = 0
if old1 in t:
    t = t.replace(old1, new1)
    print("Step 1: SUCCESS - Changed p.search to p.q")
    changes += 1
else:
    print("Step 1: ERROR - old1 not found")

if old2 in t:
    t = t.replace(old2, new2)
    print("Step 2: SUCCESS - Removed unused searchVal")
    changes += 1
else:
    print("Step 2: ERROR - old2 not found")

if old3 in t:
    t = t.replace(old3, new3)
    print("Step 3: SUCCESS - Added URL-based filter button highlight")
    changes += 1
else:
    print("Step 3: ERROR - old3 not found (already applied or changed)")

if changes > 0:
    p.write_text(t, encoding="utf-8")
    print("File saved")
else:
    print("No changes made")

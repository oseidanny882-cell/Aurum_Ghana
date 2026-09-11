import pathlib

p = pathlib.Path("c:/Users/Codewithme/jewelry-gh/frontend/scripts.js")
t = p.read_text(encoding="utf-8")

# Replace the broken initSearch function
old = '''function initSearch() {

        var inp = document.getElementById("search-input");

        if (!inp) return;

        var t;

        inp.addEventListener("input", function() {

            clearTimeout(t);

            t = setTimeout(function() {

                var q = inp.value.trim();

                if (q.length >= 2) window.location.href = "/category.html?search=" + encodeURIComponent(q);

            }, 600);

        });

    }'''

new = '''function initSearch() {

        var btn = document.getElementById("search-btn");
        var overlay = document.getElementById("search-overlay");
        var form = document.getElementById("search-form");
        var inp = document.getElementById("search-input");
        var closeBtn = document.getElementById("search-close-btn");

        // Search button is the entry point. If no button, nothing to do.
        if (!btn) return;

        // Pre-fill input if we are on category page with a search query
        if (inp) {
            try {
                var u = new URLSearchParams(window.location.search);
                var existing = u.get("search") || u.get("q");
                if (existing) inp.value = existing;
            } catch (e) { /* ignore */ }
        }

        // Open search overlay
        btn.addEventListener("click", function(e) {
            e.preventDefault();
            if (!overlay) {
                // No modal on this page, navigate to category with prompt
                var q = window.prompt("Search products:");
                if (q && q.trim()) window.location.href = "/category.html?search=" + encodeURIComponent(q.trim());
                return;
            }
            overlay.hidden = false;
            overlay.classList.add("is-open");
            setTimeout(function() { if (inp) inp.focus(); }, 50);
        });

        // Close button
        if (closeBtn && overlay) {
            closeBtn.addEventListener("click", function() {
                overlay.hidden = true;
                overlay.classList.remove("is-open");
            });
        }

        // Click on backdrop closes modal
        if (overlay) {
            overlay.addEventListener("click", function(e) {
                if (e.target === overlay) {
                    overlay.hidden = true;
                    overlay.classList.remove("is-open");
                }
            });
        }

        // Escape key closes modal
        document.addEventListener("keydown", function(e) {
            if (e.key === "Escape" && overlay && !overlay.hidden) {
                overlay.hidden = true;
                overlay.classList.remove("is-open");
            }
        });

        // Form submission - navigate to category page with search param
        if (form) {
            form.addEventListener("submit", function(e) {
                e.preventDefault();
                var q = inp ? inp.value.trim() : "";
                if (q.length < 1) return;
                // Navigate to category page with search param (preserves ?cat= if any)
                window.location.href = "/category.html?search=" + encodeURIComponent(q);
            });
        }

        // Live search as user types (debounced) - updates URL and re-fetches
        if (inp) {
            var dt;
            inp.addEventListener("input", function() {
                clearTimeout(dt);
                dt = setTimeout(function() {
                    var q = inp.value.trim();
                    // Only do live search on category page where load() exists
                    if (window.location.pathname.indexOf("category.html") === -1) return;
                    var u = new URLSearchParams(window.location.search);
                    if (q.length >= 1) {
                        u.set("search", q);
                    } else {
                        u.delete("search");
                    }
                    var newQuery = u.toString();
                    var newUrl = window.location.pathname + (newQuery ? "?" + newQuery : "");
                    window.history.pushState({}, "", newUrl);
                    if (typeof load === "function") load();
                }, 500);
            });
        }

    }'''

if old in t:
    t = t.replace(old, new)
    p.write_text(t, encoding="utf-8")
    print("SUCCESS: Replaced initSearch()")
else:
    print("ERROR: old text not found")
    # Show what's actually there
    idx = t.find("function initSearch()")
    if idx > 0:
        print(repr(t[idx:idx+800]))

/*

 * Aurum Ghana - Main Application Script

 */

(function() {

    "use strict";



    window.showToast = function(message, type, duration) {

        type = type || "info";

        duration = duration || 4000;

        var container = document.getElementById("toast-container");

        if (!container) return;

        var toast = document.createElement("div");

        toast.className = "toast " + type;

        var icons = { success: "&#10003;", error: "&#10005;", warning: "&#9888;", info: "&#8505;" };

        toast.innerHTML = "<span class=\"toast-icon\">" + (icons[type] || icons.info) + "</span><span class=\"toast-msg\">" + Security.escapeHtml(message) + "</span><button class=\"toast-close\">&times;</button>";

        container.appendChild(toast);

        toast.querySelector(".toast-close").addEventListener("click", function() { toast.remove(); });

        if (duration > 0) setTimeout(function() { toast.remove(); }, duration);

    };

    window.toast = window.showToast;



    function initMobileNav() {

        var h = document.getElementById("hamburger"), m = document.getElementById("mobile-nav");

        if (!h || !m) return;

        h.addEventListener("click", function() {

            var o = m.classList.toggle("open");

            h.classList.toggle("active", o);

            h.setAttribute("aria-expanded", o);

            document.body.style.overflow = o ? "hidden" : "";

        });

        m.querySelectorAll("a").forEach(function(l) {

            l.addEventListener("click", function() {

                m.classList.remove("open");

                h.classList.remove("active");

                h.setAttribute("aria-expanded", "false");

                document.body.style.overflow = "";

            });

        });

        document.addEventListener("keydown", function(e) {

            if (e.key === "Escape" && m.classList.contains("open")) {

                m.classList.remove("open");

                h.classList.remove("active");

                h.setAttribute("aria-expanded", "false");

                document.body.style.overflow = "";

                h.focus();

            }

        });

    }



    function initNewsletter() {

        var f = document.getElementById("newsletter-form");

        if (!f) return;

        f.addEventListener("submit", async function(e) {

            e.preventDefault();

            var m = document.getElementById("newsletter-msg"), em = f.email.value.trim();

            if (!em || !window.Security.isValidEmail(em)) {

                if (m) { m.textContent = "Please enter a valid email."; m.className = "form-msg error"; }

                return;

            }

            f.querySelector('button[type="submit"]').disabled = true;

            try {

                await window.api.request("/newsletter", { method: "POST", body: JSON.stringify({ email: em }) });

                if (m) { m.textContent = "Thank you! You're subscribed."; m.className = "form-msg success"; }

                f.reset();

            } catch(err) {

                if (m) { m.textContent = err.message || "Subscription failed."; m.className = "form-msg error"; }

            } finally { f.querySelector('button[type="submit"]').disabled = false; }

        });

    }



    window.initAuthState = function() {

        var tok = localStorage.getItem("access_token"), usr = localStorage.getItem("user"), auth = !!(tok && usr), btn = document.getElementById("account-btn");

        if (!btn) return;

        if (auth) {

            try {

                var u = JSON.parse(usr), name = u.first_name || (u.email ? u.email.split("@")[0] : "Account");

                btn.innerHTML = '<span class="account-label">' + Security.escapeHtml(name) + '</span><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>';

                btn.href = "account.html";

                btn.classList.add("account-btn--authed");

            } catch(e) {}

        } else {

            btn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg><span class="account-label">Sign In</span>';

            btn.href = "login.html";

            btn.classList.remove("account-btn--authed");

        }

    };



    // Card renderer  -  shared by all product grids

    function renderProductCard(p) {

        var b = (p.is_featured ? '<span class="badge badge-featured">Featured</span>' : '') + (p.discount_price ? '<span class="badge badge-sale">Sale</span>' : '');

        var ph = p.discount_price ? '<span class="price-current">' + Products.formatPrice(p.discount_price) + '</span><span class="price-original">' + Products.formatPrice(p.price) + '</span>' : '<span class="price-current">' + Products.formatPrice(p.price) + '</span>';

        return '<article class="product-card"><a href="product.html?id=' + encodeURIComponent(p.id) + '" class="product-link"><div class="product-image-wrap"><img src="' + (p.image || 'images/placeholder.png') + '" alt="' + Security.escapeHtml(p.name) + '" loading="lazy" onerror="this.src=\'images/placeholder.png\'">' + b + '</div><div class="product-info"><p class="product-category">' + Security.escapeHtml(p.category_name || p.category || '') + '</p><h3 class="product-name">' + Security.escapeHtml(p.name) + '</h3><div class="product-price">' + ph + '</div></div></a><button class="btn-quick-add" data-product-id="' + encodeURIComponent(p.id) + '">Add to cart</button></article>';

    }



    // Wire up Add-to-cart quick buttons on any grid container

    function wireGridButtons(container, products) {

        container.querySelectorAll(".btn-quick-add").forEach(function(b) {

            b.addEventListener("click", function(e) {

                e.preventDefault();

                var pid = decodeURIComponent(b.dataset.productId); var prod = products.find(function(x) { return x.id === pid || x.id === parseInt(pid); });

                if (prod) Cart.add(prod);

            });

        });

    }



    // Load one homepage section grid

    async function loadHomepageGrid(gridId, params) {

        var g = document.getElementById(gridId);

        if (!g) return;

        try {

            var d = await window.api.getProducts(params);

            var prods = d.items || d.products || [];

            if (!prods.length) { g.innerHTML = '<p class="empty-state">No products found.</p>'; return; }

            g.innerHTML = prods.map(renderProductCard).join("");

            wireGridButtons(g, prods);

        } catch(e) { g.innerHTML = '<p class="empty-state">Failed to load products.</p>'; }

    }



    async function initHomepage() {

        // Populate all three homepage sections in parallel

        await Promise.all([

            loadHomepageGrid("grid-new",    { "filter": "new",  limit: 4 }),

            loadHomepageGrid("grid-best",   { "filter": "best", limit: 4 }),

            loadHomepageGrid("grid-featured", { featured: true, limit: 4 }),

        ]);

    }

    async function initCategoryPage() {

        var g = document.getElementById("product-grid"), cnt = document.getElementById("product-count"), sort = document.getElementById("sort-select");
        var filterBtns = document.querySelectorAll(".filter-bar .filter-btn");

        if (!g) return;

        async function load() {

            var p = {};

            var u = new URLSearchParams(window.location.search);

            if (u.get("cat")) p.category = u.get("cat");

            if (u.get("search")) { p.q = u.get("search"); document.title = "Search: " + u.get("search") + " - Aurum Ghana"; }
            if (u.get("filter")) p.filter = u.get("filter");

            if (sort) p.sort = sort.value;

            g.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:3rem;color:var(--color-text-muted);">Loading...</div>';

            try {

                var d = await window.api.getProducts(p), prods = d.items || d.products || [];

                if (cnt) cnt.textContent = prods.length + " product" + (prods.length !== 1 ? "s" : "");

                if (!prods.length) { g.innerHTML = '<p class="empty-state" style="grid-column:1/-1;text-align:center;padding:3rem;">No products found. <a href="category.html">Browse all</a>.</p>'; return; }

                g.innerHTML = prods.map(renderProductCard).join("");

                wireGridButtons(g, prods);

            } catch(e) { g.innerHTML = '<p class="empty-state" style="grid-column:1/-1;text-align:center;padding:3rem;">Failed to load products.</p>'; }

        }

        // Set active filter button based on current URL on page load
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
        }

        window.addEventListener("popstate", load);

        if (sort) sort.addEventListener("change", load);

        load();

    }



    async function initProductPage() {

        var u = new URLSearchParams(window.location.search), id = u.get("id") || u.get("slug");

        if (!id) { window.location.href = "category.html"; return; }

        var c = document.getElementById("product-detail");

        if (!c) return;

        c.innerHTML = '<div style="text-align:center;padding:4rem;color:var(--color-text-muted);">Loading...</div>';

        try {

            var p = await window.api.getProduct(id), stock = p.stock || 0, inStock = stock > 0;

            var outMsg = stock === 0 ? "Out of stock" : (stock <= 5 ? "Only " + stock + " left" : "");

            var dropshipBadge = p.is_dropship ? '<span class="badge badge-featured">Ships from supplier</span>' : '';

            var badge = dropshipBadge || (p.is_featured ? '<span class="badge badge-featured">Featured</span>' : (p.discount_price ? '<span class="badge badge-sale">Sale</span>' : ''));

            var ph = p.discount_price ? '<span class="price-current" style="font-size:1.75rem;">' + Products.formatPrice(p.discount_price) + '</span><span class="price-original" style="font-size:1.1rem;">' + Products.formatPrice(p.price) + '</span>' : '<span class="price-current" style="font-size:1.75rem;">' + Products.formatPrice(p.price) + '</span>';

            // Build image list - use images array first, fall back to single image, then placeholder

            var imgList = (p.images && p.images.length > 0) ? p.images : [];

            if (!imgList.length && p.image) imgList = [p.image];

            var placeholderImg = 'images/placeholder.png';

            var galHtml = '<div class="gallery-main"><img id="gallery-main-img" src="' + (imgList[0] || placeholderImg) + '" alt="' + Security.escapeHtml(p.name) + '" onerror="this.src=\'' + placeholderImg + '\'"></div>';

            if (imgList.length > 1) galHtml += '<div class="gallery-thumbs">' + imgList.map(function(img, i) { return '<button class="gallery-thumb ' + (i === 0 ? 'active' : '') + '" data-src="' + img + '"><img src="' + img + '" alt="" onerror="this.src=\'' + placeholderImg + '\'"></button>'; }).join("") + '</div>';

            c.innerHTML = '<div class="product-detail-grid"><div class="product-gallery">' + galHtml + '</div><div class="product-detail-info">' + (badge ? '<div style="margin-bottom:0.75rem;">' + badge + '</div>' : '') + '<h1 class="product-detail-name">' + Security.escapeHtml(p.name) + '</h1><div class="product-detail-price">' + ph + '</div>' + (p.description ? '<p class="product-detail-desc">' + Security.escapeHtml(p.description) + '</p>' : '') + (p.is_dropship ? '<p class="dropship-notice">Ships from supplier &mdash; allow up to 14 days for delivery</p>' : '') + (outMsg ? '<p class="stock-warning">' + Security.escapeHtml(outMsg) + '</p>' : '') + '<div class="product-detail-actions"><div class="quantity-control"><button class="qty-btn" id="qty-minus">&#8722;</button><input type="number" id="qty-input" value="1" min="1" max="' + stock + '"><button class="qty-btn" id="qty-plus">+</button></div><button class="btn btn-primary btn-lg" id="btn-add-to-cart"' + (inStock ? '' : ' disabled') + '>' + (inStock ? 'Add to Cart' : 'Out of Stock') + '</button></div></div></div>';

            var mainImg = document.getElementById("gallery-main-img");

            c.querySelectorAll(".gallery-thumb").forEach(function(th) {

                th.addEventListener("click", function() {

                    mainImg.src = th.dataset.src;

                    c.querySelectorAll(".gallery-thumb").forEach(function(t) { t.classList.remove("active"); });

                    th.classList.add("active");

                });

            });

            var qI = document.getElementById("qty-input");

            document.getElementById("qty-minus").addEventListener("click", function() { qI.value = Math.max(1, parseInt(qI.value) - 1); });

            document.getElementById("qty-plus").addEventListener("click", function() { qI.value = Math.min(stock, parseInt(qI.value) + 1); });

            document.getElementById("btn-add-to-cart").addEventListener("click", function() { Cart.add(p, parseInt(qI.value)); });

        } catch(e) { console.error("[initProductPage] Error:", e); c.innerHTML = '<p class="empty-state">Product not found. <a href="category.html">Browse all</a>.</p>'; }

    }



    function initCartPage() {

        var g = document.getElementById("cart-items"), s = document.getElementById("cart-summary"), empty = document.getElementById("cart-empty");

        if (!g) return;

        function render() {

            var items = Cart.items;

            if (!items.length) {

                // Hide cart sections, show empty state

                g.style.display = "none";

                if (s) s.style.display = "none";

                if (empty) empty.style.display = "";

                return;

            }

            // Show cart sections, hide empty state

            g.style.display = "";

            if (s) s.style.display = "";

            if (empty) empty.style.display = "none";

            g.innerHTML = items.map(function(i) {

                var up = (i.discount_price && i.discount_price < i.price) ? i.discount_price : i.price;

                return '<div class="cart-item" data-key="' + Security.escapeHtml(i.key) + '"><a href="product.html?id=' + encodeURIComponent(i.product_id) + '"><img src="' + Security.escapeHtml(i.image || "") + '" alt="' + Security.escapeHtml(i.name) + '" onerror="this.src=\'images/placeholder.png\'" class="cart-item-img"></a><div class="cart-item-info"><a href="product.html?id=' + encodeURIComponent(i.product_id) + '" class="cart-item-name">' + Security.escapeHtml(i.name) + '</a><p class="cart-item-price">' + Products.formatPrice(up) + '</p></div><div class="cart-item-qty"><button class="qty-btn qty-btn-sm" data-action="minus">&#8722;</button><input type="number" value="' + i.quantity + '" min="1" max="' + i.stock + '" class="qty-input-sm"><button class="qty-btn qty-btn-sm" data-action="plus">+</button></div><div class="cart-item-total">' + Products.formatPrice(up * i.quantity) + '</div><button class="cart-item-remove" data-key="' + Security.escapeHtml(i.key) + '">&times;</button></div>';

            }).join("");

            g.querySelectorAll(".qty-btn").forEach(function(b) {

                b.addEventListener("click", function() {

                    var el = b.closest(".cart-item"), k = el.dataset.key, it = Cart.items.find(function(x) { return x.key === k; });

                    if (!it) return;

                    if (b.dataset.action === "plus") Cart.update(k, it.quantity + 1);

                    else Cart.update(k, it.quantity - 1);

                });

            });

            g.querySelectorAll(".qty-input-sm").forEach(function(inp) {

                inp.addEventListener("change", function() { Cart.update(inp.closest(".cart-item").dataset.key, parseInt(inp.value) || 1); });

            });

            g.querySelectorAll(".cart-item-remove").forEach(function(b) {

                b.addEventListener("click", function() { Cart.remove(b.dataset.key); });

            });

            if (s) s.innerHTML = '<h2>Summary</h2><div class="cart-line"><span>Subtotal</span><span>' + Products.formatPrice(Cart.subtotal) + '</span></div><div class="cart-line"><span>Delivery</span><span>' + (Cart.delivery_fee === 0 ? "Free" : Products.formatPrice(Cart.delivery_fee)) + '</span></div>' + (Cart.discount > 0 ? '<div class="cart-line"><span>Discount</span><span>-' + Products.formatPrice(Cart.discount) + '</span></div>' : '') + '<div class="cart-line total"><span>Total</span><span>' + Products.formatPrice(Cart.total) + '</span></div><a href="' + (window.Auth && window.Auth.isAuthenticated ? 'checkout.html' : 'login.html?redirect=checkout.html') + '" class="btn btn-primary btn-block mt-4" id="cart-proceed-checkout">' + (window.Auth && window.Auth.isAuthenticated ? 'Proceed to checkout' : 'Login to checkout') + '</a>';

        }

        render();

        document.addEventListener("cart:updated", render);

    }

    function initSearch() {

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
                if (q && q.trim()) window.location.href = "category.html?search=" + encodeURIComponent(q.trim());
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
                window.location.href = "category.html?search=" + encodeURIComponent(q);
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

    }

    function initLogout() {

        var link = document.getElementById("logout-link");

        if (!link) return;

        link.addEventListener("click", async function(e) {

            e.preventDefault();

            if (window.Auth && window.Auth.logout) await window.Auth.logout();

            if (window.initAuthState) window.initAuthState();

            window.location.href = "index.html";

        });

    }

    document.addEventListener("DOMContentLoaded", async function() {

        await window.Auth?.init();

        Cart.init();

        if (window.initAuthState) window.initAuthState();

        initMobileNav();

        initNewsletter();

        initSearch();

        initLogout();

        var page = document.body.dataset.page;

        if (page === "home")      await initHomepage();

        if (page === "category")  await initCategoryPage();

        if (page === "product")   await initProductPage();

        if (page === "cart")      initCartPage();

        if (page === "checkout" && window.Checkout) window.Checkout.init();

        if (page === "admin" && window.Admin)         window.Admin.init();

        window.addEventListener("resize", function() {

            var m = document.getElementById("mobile-nav"), h = document.getElementById("hamburger");

            if (window.innerWidth >= 1024 && m && m.classList.contains("open")) {

                m.classList.remove("open");

                if (h) { h.classList.remove("active"); h.setAttribute("aria-expanded", "false"); }

                document.body.style.overflow = "";

            }

        });

    });

})();


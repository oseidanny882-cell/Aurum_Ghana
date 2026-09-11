/*
 * Aurum Ghana - Products Module
 * Product rendering and helpers
 */

const Products = {
    // Format GHS price
    formatPrice(amount) {
        const num = Number(amount) || 0;
        return new Intl.NumberFormat("en-GH", {
            style: "currency",
            currency: "GHS",
            minimumFractionDigits: 2,
        }).format(num);
    },

    // Render a product card
    renderCard(product, opts = {}) {
        const S = window.Security;
        const hasDiscount = product.discount_price && product.discount_price < product.price;
        const price = hasDiscount ? product.discount_price : product.price;
        const isOut = (product.stock ?? 1) <= 0;
        const isDropship = !!product.is_dropship;
        const badge = isOut
            ? `<span class="product-badge out">Out of stock</span>`
            : product.is_featured
            ? `<span class="product-badge">Featured</span>`
            : hasDiscount
            ? `<span class="product-badge sale">Sale</span>`
            : (product.is_new ? `<span class="product-badge">New</span>` : isDropship ? `<span class="product-badge dropship">Ships from supplier</span>` : "");
        const img = S.escapeHtml(product.images?.[0] || product.image || "");
        const name = S.escapeHtml(product.name);
        const nameDisplay = isDropship ? `${name} <span class=\"text-muted\" style=\"font-size:0.75em\">[Ships from supplier]</span>` : name;
        const cat = S.escapeHtml(product.category || "");
        const slug = S.escapeHtml(product.slug || product.id);
        const stockAttr = isOut ? `disabled` : "";
        return `
            <article class="product-card">
                <a href="product.html?slug=${encodeURIComponent(slug)}" aria-label="${name}">
                    <div class="product-img">
                        ${badge}
                        <img src="${img}" alt="${name}" loading="lazy" onerror="this.style.display='none'">
                    </div>
                </a>
                <div class="product-info">
                    <p class="product-cat">${cat}</p>
                    <h3 class="product-name">
                        <a href="product.html?slug=${encodeURIComponent(slug)}">${nameDisplay}</a>
                    </h3>
                    <div class="product-price">
                        <span class="price-current">${this.formatPrice(price)}</span>
                        ${hasDiscount ? `<span class="price-original">${this.formatPrice(product.price)}</span>` : ""}
                    </div>
                </div>
                <button class="product-quick" data-product-id="${S.escapeHtml(product.id)}" data-product-slug="${slug}" ${stockAttr}>
                    ${isOut ? "Out of stock" : "Add to cart"}
                </button>
            </article>
        `;
    },

    // Render grid to element
    renderGrid(products, targetEl) {
        if (!targetEl) return;
        if (!products || products.length === 0) {
            targetEl.innerHTML = `<p class="text-muted text-center" style="grid-column: 1/-1; padding: 2rem;">No products found.</p>`;
            return;
        }
        targetEl.innerHTML = products.map(p => this.renderCard(p)).join("");
        this.attachQuickAdd(targetEl);
    },

    // Attach quick-add listeners
    attachQuickAdd(gridEl) {
        gridEl.querySelectorAll(".product-quick").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                e.preventDefault();
                if (btn.disabled) return;
                const productId = btn.dataset.productId;
                const productSlug = btn.dataset.productSlug;
                try {
                    btn.disabled = true;
                    btn.textContent = "Adding...";
                    // Fetch the real product from the API so we have stock, image, etc.
                    let productData = null;
                    try {
                        // Determine endpoint: prefer slug > productId > extract from DOM link
                        let endpoint = null;
                        if (productSlug) {
                            endpoint = `/products/${productSlug}`;
                        } else if (productId) {
                            endpoint = `/products/${productId}`;
                        } else {
                            // Last resort: extract id/slug from the product card link
                            const card = btn.closest(".product-card");
                            const link = card?.querySelector(".product-name a");
                            if (link) {
                                const linkUrl = new URL(link.href, window.location.href);
                                endpoint = `/products/${linkUrl.searchParams.get("slug") || linkUrl.searchParams.get("id")}`;
                            }
                        }
                        if (endpoint) productData = await window.api.request(endpoint);
                    } catch (fetchErr) {
                        // Fall back to scraping from DOM if API fails
                        const productCard = btn.closest(".product-card");
                        const name = productCard?.querySelector(".product-name a")?.textContent || "Product";
                        const priceText = productCard?.querySelector(".price-current")?.textContent.replace(/[^\d.]/g, "") || "0";
                        const price = parseFloat(priceText) || 0;
                        const img = productCard?.querySelector(".product-img img")?.src || "";
                        productData = { id: productId, name, price, image: img, stock: 99 };
                    }
                    const success = window.Cart.add(productData, 1);
                    if (!success) btn.textContent = "Out of stock";
                } catch (err) {
                    console.error("[QuickAdd] Error:", err);
                    showToast("Failed to add to cart", "error");
                } finally {
                    btn.disabled = false;
                    if (btn.textContent === "Adding...") btn.textContent = "Add to cart";
                }
            });
        });
    },

    // Fetch from API with fallback to mock data
    async fetch(params = {}) {
        try {
            const data = await window.api.getProducts(params);
            return data.items || data.products || data;
        } catch (e) {
            // Fallback to local mock data
            return this.getMockData(params);
        }
    },

    getMockData(params = {}) {
        const all = this.getSeedProducts();
        let filtered = all;
        if (params.cat) filtered = filtered.filter(p => p.category === params.cat);
        if (params.filter === "new") filtered = filtered.filter(p => p.is_new);
        if (params.filter === "best") filtered = filtered.filter(p => p.is_best);
        if (params.featured === "true") filtered = filtered.filter(p => p.featured);
        if (params.search) {
            const s = params.search.toLowerCase();
            filtered = filtered.filter(p => p.name.toLowerCase().includes(s));
        }
        return filtered;
    },

    getSeedProducts() {
        // Lightweight seed for frontend demo. Backend is authoritative.
        const cats = ["rings", "necklaces", "bracelets", "earrings"];
        const names = {
            rings: ["Aurora Solitaire", "Twilight Band", "Heritage Signet", "Luna Crescent", "Sahara Circle", "Golden Promise", "Eternal Knot", "Diamond Whisper", "Royal Crest", "Sunset Halo"],
            necklaces: ["Starlight Pendant", "Golden Tassel", "Moonstone Chain", "Heritage Choker", "Pearl Whisper", "Akan Pendant", "Eternal Link", "Desert Bloom", "Twilight Drop", "Sunset Strand"],
            bracelets: ["Golden Bangle", "Beaded Heritage", "Twisted Chain", "Pearl Strand", "Cuff of Grace", "Lagos Braid", "Ankoma Weave", "Sunset Cuff", "Kente Charm", "Eternal Loop"],
            earrings: ["Pearl Drop", "Golden Hoop", "Sunset Stud", "Twilight Drop", "Heritage Stud", "Moonstone Halo", "Diamond Whisper", "Crescent Glow", "Royal Stud", "Akan Loop"],
        };
        const colors = ["Gold", "Rose Gold", "Silver", "Mixed"];
        const products = [];
        let i = 0;
        for (const cat of cats) {
            for (const name of names[cat]) {
                const price = 80 + Math.floor(Math.random() * 800) + 0.99;
                const hasDiscount = i % 7 === 0;
                products.push({
                    id: `sku-${cat}-${i + 1}`,
                    sku: `AG-${cat.toUpperCase().slice(0, 3)}-${String(i + 1).padStart(4, "0")}`,
                    slug: `${cat}-${name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`,
                    name,
                    category: cat,
                    price,
                    discount_price: hasDiscount ? price * 0.75 : null,
                    currency: "GHS",
                    stock: 5 + Math.floor(Math.random() * 30),
                    image: `/images/${cat}-${(i % 10) + 1}.jpg`,
                    images: [`/images/${cat}-${(i % 10) + 1}.jpg`],
                    material: ["Gold-plated", "Sterling Silver", "Brass", "Mixed metals"][i % 4],
                    color: colors[i % colors.length],
                    is_new: i < 12,
                    is_best: i % 5 === 0,
                    featured: i % 4 === 0,
                });
                i++;
            }
        }
        return products;
    },
};

window.Products = Products;

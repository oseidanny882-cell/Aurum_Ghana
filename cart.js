/* Aurum Ghana - Cart Module */
const CART_KEY = "aurum_cart";
const Cart = {
    items: [], subtotal: 0, delivery_fee: 0, discount: 0, total: 0,
    init() { this.load(); this.updateBadge(); this.loadFromBackend(); },
    load() {
        try { const stored = localStorage.getItem(CART_KEY); this.items = stored ? JSON.parse(stored) : []; } catch { this.items = []; }
        this.recalculate();
    },
    save() {
        localStorage.setItem(CART_KEY, JSON.stringify(this.items));
        this.recalculate(); this.updateBadge();
        document.dispatchEvent(new CustomEvent("cart:updated", { detail: { cart: this } }));
        // Sync to backend if user is logged in
        this._syncToBackend();
    },
    async _syncToBackend() {
        if (!window.Auth?.isAuthenticated || window.Auth?.mfaPending) return;
        try {
            await window.api.clearCart();
            for (const item of this.items) {
                await window.api.addToCart(item.product_id, item.quantity, item.variant_id);
            }
        } catch { /* silent fail - offline or not logged in */ }
    },
    async loadFromBackend() {
        if (!window.Auth?.isAuthenticated || window.Auth?.mfaPending) return;
        if (location.pathname.match(/\/(login|mfa|register|forgot-password|reset-password)\.html$/)) return;
        try {
            const data = await window.api.getCart();
            const items = data.items || [];
            if (items.length === 0) return;
            for (const item of items) {
                const key = `${item.product_id}_${item.variant_id || "default"}`;
                if (!this.items.find(i => i.key === key)) {
                    this.items.push({ key, product_id: item.product_id, slug: item.slug, name: item.name, image: item.image, price: item.price, discount_price: item.discount_price, quantity: item.quantity, variant_id: item.variant_id, stock: item.stock ?? 99 });
                }
            }
            this.save();
        } catch { /* silent fail */ }
    },
    add(product, quantity = 1, variantId = null) {
        const itemKey = `${product.id}_${variantId || "default"}`;
        const existing = this.items.find(i => i.key === itemKey);
        const stock = product.stock ?? 99;
        const requested = existing ? existing.quantity + quantity : quantity;
        if (requested > stock) { showToast(`Only ${stock} in stock for ${product.name}`, "warning"); return false; }
        if (existing) { existing.quantity = requested; } else {
            this.items.push({ key: itemKey, product_id: product.id, slug: product.slug, name: product.name, image: product.images?.[0] || product.image, price: product.price, discount_price: product.discount_price, quantity: Math.min(quantity, stock), variant_id: variantId, stock });
        }
        this.save(); showToast(`${product.name} added to cart`, "success"); return true;
    },
    update(itemKey, quantity) {
        const item = this.items.find(i => i.key === itemKey);
        if (!item) return;
        if (quantity <= 0) { this.remove(itemKey); return; }
        if (quantity > item.stock) { showToast(`Only ${item.stock} available`, "warning"); quantity = item.stock; }
        item.quantity = quantity; this.save();
    },
    remove(itemKey) { this.items = this.items.filter(i => i.key !== itemKey); this.save(); },
    clear() { this.items = []; this.save(); },
    count() { return this.items.reduce((sum, i) => sum + i.quantity, 0); },
    recalculate() {
        this.subtotal = this.items.reduce((sum, i) => { const unit = (i.discount_price && i.discount_price < i.price) ? i.discount_price : i.price; return sum + unit * i.quantity; }, 0);
        this.delivery_fee = this.subtotal > 0 ? (this.subtotal >= 500 ? 0 : 30) : 0;
        this.discount = 0; this.total = this.subtotal + this.delivery_fee - this.discount;
    },
    updateBadge() {
        const el = document.getElementById("cart-count");
        if (el) { const n = this.count(); el.textContent = n; el.setAttribute("data-count", n); }
    },
};
window.Cart = Cart;

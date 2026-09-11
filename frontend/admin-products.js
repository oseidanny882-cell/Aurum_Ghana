/**
 * Aurum Ghana - Admin Products Module
 * Full CRUD for products with modal form
 */

const AdminProducts = {
  editingId: null,
  categories: [],
  suppliers: [],

  async init() {
    // CRITICAL: wait for Auth.init() to finish before checking admin status.
    // Auth.init() loads user from localStorage and verifies the token against
    // the backend. Without this await, redirectIfNotAdmin() can run before
    // Auth.user is populated (or after a failed verify cleared it), causing
    // a logged-in admin to be redirected back to the home page -- especially
    // when navigating via the browser back button.
    await Auth.init();
    if (!Auth.redirectIfNotAdmin()) return;
    this.bindModal();
    this.bindEvents();
    await Promise.all([this.loadCategories(), this.loadSuppliers()]);
    await this.loadProducts();
  },

  bindEvents() {
    document.getElementById("add-product-btn")?.addEventListener("click", () => this.openModal());
    document.getElementById("product-form")?.addEventListener("submit", e => { e.preventDefault(); this.handleSubmit(); });
    document.getElementById("p-name")?.addEventListener("input", e => {
      if (!this.editingId) {
        const s = e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
        const slugEl = document.getElementById("p-slug");
        if (slugEl) slugEl.value = s;
      }
    });
    // Image file input: show local preview immediately
    document.getElementById("p-img")?.addEventListener("change", e => this.handleImageSelect(e));
    document.getElementById("img-remove-btn")?.addEventListener("click", () => this.clearImage());
    // Show Inactive Products toggle
    const cb = document.getElementById("show-inactive-cb");
    if (cb) {
      cb.addEventListener("change", () => this.loadProducts(1));
    }
  },

  handleImageSelect(e) {
    var file = e.target.files && e.target.files[0];
    if (!file) return;
    var errEl = document.getElementById("img-error");
    var preview = document.getElementById("img-preview");
    var wrap = document.getElementById("img-preview-wrap");
    var infoEl = document.getElementById("img-info");
    var nameEl = document.getElementById("img-filename");

    // Client-side file size validation (5 MB limit)
    if (file.size > 5 * 1024 * 1024) {
      if (errEl) {
        errEl.textContent = "File is too large (" + Math.round(file.size / 1024 / 1024 * 10) / 10 + " MB). Maximum is 5 MB.";
        errEl.style.display = "block";
      }
      this.clearImage();
      return;
    }
    if (errEl) errEl.style.display = "none";

    // Show filename next to the choose button
    if (nameEl) nameEl.textContent = file.name + " (" + Math.round(file.size / 1024) + " KB)";

    // Read the image, get true dimensions, then show the preview
    var reader = new FileReader();
    reader.onload = function(ev) {
      var img = new Image();
      img.onload = function() {
        if (infoEl) infoEl.textContent = img.width + " x " + img.height + " px";
        if (preview) preview.src = ev.target.result;
        if (wrap) wrap.style.display = "block";
      };
      img.src = ev.target.result;
    };
    reader.readAsDataURL(file);
  },

  clearImage() {
    var fileInput = document.getElementById("p-img");
    var urlInput = document.getElementById("p-img-url");
    var nameEl = document.getElementById("img-filename");
    var wrap = document.getElementById("img-preview-wrap");
    var errEl = document.getElementById("img-error");
    if (fileInput) fileInput.value = "";
    if (urlInput) urlInput.value = "";
    if (nameEl) nameEl.textContent = "";
    if (wrap) wrap.style.display = "none";
    if (errEl) errEl.style.display = "none";
  },

  showImagePreview(url) {
    var preview = document.getElementById("img-preview");
    var wrap = document.getElementById("img-preview-wrap");
    if (preview) preview.src = url;
    if (wrap) wrap.style.display = url ? "block" : "none";
  },

  bindModal() {
    const m = document.getElementById("product-modal");
    document.getElementById("modal-close")?.addEventListener("click", () => this.closeModal());
    document.getElementById("form-cancel")?.addEventListener("click", () => this.closeModal());
    m?.addEventListener("click", e => { if (e.target === m) this.closeModal(); });
    document.addEventListener("keydown", e => { if (e.key === "Escape" && m && m.style.display !== "none") this.closeModal(); });
  },

  async loadCategories() {
    try { const d = await window.api.getCategories(); this.categories = d.items || []; }
    catch (e) { this.categories = []; }
    const sel = document.getElementById("p-cat");
    if (sel) sel.innerHTML = '<option value="">-- Select --</option>' + this.categories.map(c => '<option value="' + Security.escapeHtml(c.slug) + '">' + Security.escapeHtml(c.name) + '</option>').join("");
  },

  async loadSuppliers() {
    try { const d = await window.api.getSuppliers({ per_page: 500 }); this.suppliers = d.items || []; }
    catch (e) { this.suppliers = []; }
    const sel = document.getElementById("p-sup");
    if (sel) sel.innerHTML = '<option value="">-- None --</option>' + this.suppliers.map(s => '<option value="' + Security.escapeHtml(s.id) + '">' + Security.escapeHtml(s.name) + '</option>').join("");
  },

  async loadProducts(page) {
    if (!page) page = 1;
    const w = document.getElementById("products-table");
    w.innerHTML = '<p style="padding:20px;text-align:center;color:#888;">Loading...</p>';
    try {
      const showInactive = document.getElementById("show-inactive-cb")?.checked || false;
      const params = new URLSearchParams(location.search);
      const data = await window.api.getAdminProducts({
        page: page,
        per_page: 20,
        q: params.get("q") || undefined,
        category: params.get("category") || undefined,
        is_active: showInactive ? "false" : undefined
      });
      console.log("[AdminProducts] Loaded data:", data);
      // Update filter status text
      const filterEl = document.getElementById("filter-status");
      if (filterEl) {
        filterEl.textContent = showInactive ? "Showing all products (including inactive)" : "Showing active products only";
      }
      this.renderTable(data);
    } catch (e) {
      console.error("[AdminProducts] Failed to load products:", e);
      w.innerHTML = '<p style="padding:20px;color:red;">Failed to load: ' + Security.escapeHtml(e.message) + '</p>'
        + '<p style="padding:0 20px 20px;font-size:11px;color:#888;">URL params: page=' + page + '</p>';
    }
  },


  renderTable(data) {
    // Defensive: handle both "items" and "products" keys from backend
    var items = (data && (data.items || data.products)) || [];
    var total = (data && data.total) || items.length;
    var page = (data && data.page) || 1;
    var pages = (data && data.pages) || 1;
    var w = document.getElementById("products-table");
    if (!items.length) {
      // Show debug info so we can diagnose empty-list issues
      console.warn("[AdminProducts] Empty product list. Response:", data);
      w.innerHTML = '<p style="padding:40px;text-align:center;color:#888;">No products found.</p>'
        + '<p style="padding:0 40px 20px;font-size:11px;color:#aaa;text-align:center;">(Check browser console for details. Response keys: '
        + (data ? Object.keys(data).join(", ") : "no data") + ')</p>';
      return;
    }
    var self = this;
    var rows = items.map(function(p) {
      var img = p.image ? '<img src="' + p.image + '" alt="" style="width:48px;height:48px;object-fit:cover;border-radius:4px;">' : '<div style="width:48px;height:48px;background:#eee;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:12px;color:#888;">?</div>';
      var flags = (p.is_new ? '<span style="font-size:11px;padding:1px 6px;background:#e3f2fd;color:#1565c0;border-radius:3px;margin-right:4px;">New</span>' : '') +
        (p.is_best ? '<span style="font-size:11px;padding:1px 6px;background:#fff3e0;color:#e65100;border-radius:3px;margin-right:4px;">Best</span>' : '') +
        (p.is_featured ? '<span style="font-size:11px;padding:1px 6px;background:#fce4ec;color:#880e4f;border-radius:3px;margin-right:4px;">Featured</span>' : '') +
        (!p.is_active ? '<span style="font-size:11px;padding:1px 6px;background:#f5f5f5;color:#999;border-radius:3px;margin-right:4px;">Inactive</span>' : '');
      var price = p.discount_price ? '<span style="text-decoration:line-through;color:#999;">' + window.Products.formatPrice(p.price) + '</span><br><strong style="color:#c62828;">' + window.Products.formatPrice(p.discount_price) + '</strong>' : '<strong>' + window.Products.formatPrice(p.price) + '</strong>';
      var stock = p.stock > 0 ? '<span style="color:#2e7d32;">' + p.stock + '</span>' : '<span style="color:#c62828;">Out of stock</span>';
      return '<tr style="border-bottom:1px solid #f0f0f0;">' +
        '<td style="padding:10px 8px;">' + img + '</td>' +
        '<td style="padding:10px 8px;"><strong>' + self.esc(p.name) + '</strong><br><span style="font-size:12px;color:#888;">' + self.esc(p.sku) + '</span>' + (p.is_dropship ? '<br><span style="font-size:10px;padding:1px 6px;background:#e8f5e9;color:#2e7d32;border-radius:3px;">Dropship</span>' : '') + '</td>' +
        '<td style="padding:10px 8px;color:#666;">' + (p.category_name || '--') + '</td>' +
        '<td style="padding:10px 8px;">' + price + '</td>' +
        '<td style="padding:10px 8px;">' + stock + '</td>' +
        '<td style="padding:10px 8px;">' + flags + '</td>' +
        '<td style="padding:10px 8px;white-space:nowrap;">' +
          '<button onclick="AdminProducts.openModal(\'' + p.id + '\')" style="padding:4px 10px;font-size:12px;cursor:pointer;background:#e3f2fd;color:#1565c0;border:1px solid #bbdefb;border-radius:4px;">Edit</button> ' +
          '<button onclick="AdminProducts.handleDelete(\'' + p.id + '\')" style="padding:4px 10px;font-size:12px;cursor:pointer;background:#ffebee;color:#c62828;border:1px solid #ffcdd2;border-radius:4px;">Delete</button>' +
        '</td></tr>';
    }).join("");
    w.innerHTML = '<table style="width:100%;border-collapse:collapse;"><thead><tr style="border-bottom:2px solid #eee;text-align:left;">' +
      '<th style="padding:12px 8px;">Image</th><th style="padding:12px 8px;">Name/SKU</th><th style="padding:12px 8px;">Category</th><th style="padding:12px 8px;">Price</th><th style="padding:12px 8px;">Stock</th><th style="padding:12px 8px;">Flags</th><th style="padding:12px 8px;">Actions</th>' +
      '</tr></thead><tbody>' + rows + '</tbody></table>';
    if (pages > 1) {
      w.innerHTML += '<div style="padding:16px;display:flex;justify-content:center;gap:8px;flex-wrap:wrap;">' +
        '<button onclick="AdminProducts.loadProducts(' + (page - 1) + ')"' + (page <= 1 ? ' disabled' : '') + ' style="padding:6px 12px;cursor:pointer;">&laquo; Prev</button>' +
        '<span style="padding:6px 12px;">Page ' + page + ' of ' + pages + ' (' + total + ' total)</span>' +
        '<button onclick="AdminProducts.loadProducts(' + (page + 1) + ')"' + (page >= pages ? ' disabled' : '') + ' style="padding:6px 12px;cursor:pointer;">Next &raquo;</button>' +
      '</div>';
    }
    w.innerHTML += '<p style="padding:8px;font-size:12px;color:#888;">' + total + ' product' + (total !== 1 ? 's' : '') + '</p>';
  },


  async openModal(id) {
    this.editingId = id || null;
    document.getElementById("modal-title").textContent = id ? "Edit Product" : "Add Product";
    document.getElementById("form-submit").textContent = id ? "Update Product" : "Save Product";
    document.getElementById("product-form").reset();
    this.clearImage();
    if (id) {
      try {
        var p = await window.api.getAdminProduct(id);
        var f = function(id2, val) { var el = document.getElementById(id2); if (el) el.value = (val !== null && val !== undefined) ? val : ""; };
        f("p-name", p.name); f("p-sku", p.sku); f("p-slug", p.slug); f("p-desc", p.description);
        f("p-cat", p.category); f("p-price", p.price); f("p-disc", p.discount_price);
        f("p-stock", p.stock); f("p-mat", p.material); f("p-color", p.color);
        f("p-wt", p.weight_grams); f("p-dim", p.dimensions);
        // Show existing product image in preview
        if (p.image) {
          this.showImagePreview(p.image);
        }
        f("p-tags", Array.isArray(p.tags) ? p.tags.join(", ") : "");
        f("p-sup", p.supplier_id || "");
        f("p-cost", p.cost_price || "");
        document.getElementById("p-new").checked = !!p.is_new;
        document.getElementById("p-best").checked = !!p.is_best;
        document.getElementById("p-feat").checked = !!p.is_featured;
        document.getElementById("p-active").checked = !!p.is_active;
        var fm = p.fulfillment_mode || "in_stock";
        document.querySelectorAll('input[name="fulfillment_mode"]').forEach(function(r) { r.checked = r.value === fm; });
      } catch (e) {
        this.showToast("Failed to load product: " + e.message, "error");
        return;
      }
    }
    document.getElementById("product-modal").style.display = "flex";
    var nameEl = document.getElementById("p-name");
    if (nameEl) nameEl.focus();
  },

  closeModal() {
    var m = document.getElementById("product-modal");
    if (m) m.style.display = "none";
    this.editingId = null;
  },

  async handleSubmit() {
    var fd = new FormData(document.getElementById("product-form"));
    var getNum = function(k) { var v = fd.get(k); return v ? parseFloat(v) : null; };

    // Upload image first if a file was selected
    var imageFile = document.getElementById("p-img").files[0];
    var imageUrl = fd.get("image") || "";  // existing URL (from hidden field or edit mode)
    if (imageFile) {
      var btn = document.getElementById("form-submit");
      btn.disabled = true;
      btn.textContent = "Uploading image...";
      try {
        var upload = await window.api.uploadImage(imageFile);
        imageUrl = upload.url;
        this.showToast("Image uploaded!", "success");
      } catch (e) {
        btn.disabled = false;
        btn.textContent = this.editingId ? "Update Product" : "Save Product";
        this.showToast("Image upload failed: " + e.message, "error");
        return;
      }
    }

    var data = {
      name: fd.get("name"),
      sku: fd.get("sku"),
      price: parseFloat(fd.get("price"))
    };
    if (fd.get("slug")) data.slug = fd.get("slug");
    if (fd.get("description")) data.description = fd.get("description");
    if (fd.get("category")) data.category = fd.get("category");
    var dp = getNum("discount_price"); if (dp !== null) data.discount_price = dp;
    if (fd.get("stock")) data.stock = parseInt(fd.get("stock"));
    if (fd.get("material")) data.material = fd.get("material");
    if (fd.get("color")) data.color = fd.get("color");
    if (imageUrl) data.image = imageUrl;
    var wg = getNum("weight_grams"); if (wg !== null) data.weight_grams = wg;
    if (fd.get("dimensions")) data.dimensions = fd.get("dimensions");
    if (fd.get("tags")) data.tags = fd.get("tags");
    if (fd.get("supplier_id")) data.supplier_id = fd.get("supplier_id");
    var cp = getNum("cost_price"); if (cp !== null) data.cost_price = cp;
    data.fulfillment_mode = fd.get("fulfillment_mode") || "in_stock";
    data.is_new = fd.get("is_new") === "true";
    data.is_best = fd.get("is_best") === "true";
    data.is_featured = fd.get("is_featured") === "true";
    data.is_active = fd.get("is_active") === "true";
    var btn = document.getElementById("form-submit");
    btn.disabled = true;
    btn.textContent = "Saving...";
    try {
      if (this.editingId) {
        await window.api.updateProduct(this.editingId, data);
        this.showToast("Product updated successfully");
      } else {
        await window.api.createProduct(data);
        this.showToast("Product created successfully");
      }
      this.closeModal();
      this.loadProducts();
    } catch (e) {
      this.showToast(e.message || "Failed to save product", "error");
    } finally {
      btn.disabled = false;
      btn.textContent = this.editingId ? "Update Product" : "Save Product";
    }
  },

  async handleDelete(id) {
    if (!confirm("Delete this product? This cannot be undone.")) return;
    try {
      await window.api.deleteProduct(id);
      this.showToast("Product deleted");
      this.loadProducts();
    } catch (e) {
      this.showToast(e.message || "Failed to delete", "error");
    }
  },

  showToast(msg, type) {
    if (!type) type = "success";
    var c = document.getElementById("toast-container");
    var el = document.createElement("div");
    el.textContent = msg;
    el.style.cssText = "padding:12px 20px;margin:8px;border-radius:4px;font-size:14px;background:" + (type === "error" ? "#ffebee;color:#c62828;" : "#e8f5e9;color:#2e7d32;") + "animation:fadeIn .3s;";
    c.appendChild(el);
    setTimeout(function() { el.style.opacity = "0"; setTimeout(function() { el.remove(); }, 300); }, 3000);
  },

  esc(s) {
    if (!s) return "";
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
};

window.AdminProducts = AdminProducts;
document.addEventListener("DOMContentLoaded", function() { AdminProducts.init(); });

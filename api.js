/*
 * Aurum Ghana - API Client
 * Secure API communication with the backend
 */

    // Production backend API base URL.
    // Set window.API_BASE_URL inline before loading api.js, e.g.:
    //   <script>window.API_BASE_URL="https://your-backend.example.com/api/v1";</script>
    // If not set, the hostname-specific defaults below are used.
    // IMPORTANT: when the backend is live, update _defaultProductionApiBase
    // below to the real backend origin (NOT the GitHub Pages origin).
    const _defaultProductionApiBase = "https://web-production-b4e16.up.railway.app/api/v1";


    const API_BASE = window.API_BASE_URL
        ? window.API_BASE_URL
        : window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
            ? "http://127.0.0.1:5000/api/v1"
            : window.location.hostname === "oseidanny882-cell.github.io"
                ? _defaultProductionApiBase
                : "/api/v1";

class ApiClient {
    constructor() {
        this.baseUrl = API_BASE;
        this.csrfToken = null;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            "Content-Type": "application/json",
            "X-Request-ID": this.generateRequestId(),
            ...options.headers,
        };

        // Add CSRF token for state-changing requests (required by Flask-JWT-Extended cookie auth)
        const csrfToken = this.getCsrfToken();
        if (csrfToken && ["POST", "PUT", "PATCH", "DELETE"].includes(options.method || "GET")) {
            headers["X-CSRFToken"] = csrfToken;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
                credentials: "include",
            });

            // Handle 401 - attempt refresh
            if (response.status === 401 && !options._retry) {
                options._retry = true;
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    return this.request(endpoint, options);
                }
            }

            const data = await response.json().catch(() => ({}));

            // Cache CSRF token from response so subsequent requests can use it
            if (data.csrf_token) {
                this.csrfToken = data.csrf_token;
            }

            if (!response.ok) {
                const error = new Error(data.detail || data.message || "Request failed");
                error.status = response.status;
                error.code = data.code;
                error.data = data;
                throw error;
            }

            return data;
        } catch (error) {
            if (error.name === "TypeError") {
                throw new Error("Network error. Please check your connection.");
            }
            throw error;
        }
    }

    generateRequestId() {
        // crypto.randomUUID() is supported in all modern browsers and is
        // cryptographically random  -  not guessable like Math.random().
        if (window.crypto && window.crypto.randomUUID) {
            return window.crypto.randomUUID();
        }
        // Fallback for older environments
        return `${Date.now().toString(36)}-${Math.random().toString(36).substr(2, 9)}`;
    }

    getCsrfToken() {
        // Use the CSRF token cached from the most recent API response,
        // since document.cookie won't work for cross-origin requests.
        if (this.csrfToken) {
            return this.csrfToken;
        }
        // Fall back to reading from document.cookie (same-origin only)
        return document.cookie.match(/csrf_token=([^;]+)/)?.[1]
            || document.cookie.match(/csrftoken=([^;]+)/)?.[1]
            || null;
    }

    async refreshToken() {
        try {
            const response = await fetch(`${this.baseUrl}/auth/refresh`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
            });

            if (response.ok) {
                const data = await response.json().catch(() => ({}));
                if (data.csrf_token) {
                    this.csrfToken = data.csrf_token;
                }
                return true;
            }
        } catch {
            // Refresh failed - do NOT log out the user
        }
        return false;
    }

    // Auth
    async register(data) { return this.request("/auth/register", { method: "POST", body: JSON.stringify(data) }); }
    async login(email, password) { return this.request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }); }
    async logout() {
        try { await this.request("/auth/logout", { method: "POST" }); } catch {}
        this.csrfToken = null;
    }
    async forgotPassword(email) { return this.request("/auth/forgot-password", { method: "POST", body: JSON.stringify({ email }) }); }
    async resetPassword(token, password) { return this.request("/auth/reset-password", { method: "POST", body: JSON.stringify({ token, password }) }); }
    async verifyEmail(token) { return this.request("/auth/verify-email", { method: "POST", body: JSON.stringify({ token }) }); }
    async getProfile() { return this.request("/user/profile"); }
    async updateProfile(data) { return this.request("/user/profile", { method: "PATCH", body: JSON.stringify(data) }); }
    async changePassword(data) { return this.request("/user/change-password", { method: "POST", body: JSON.stringify(data) }); }

    // MFA
    async mfaSetup() { return this.request("/mfa/setup", { method: "POST" }); }
    async mfaVerify(code) { return this.request("/mfa/verify", { method: "POST", body: JSON.stringify({ code }) }); }
    async mfaDisable(code) { return this.request("/mfa/disable", { method: "POST", body: JSON.stringify({ code }) }); }
    // Admin email-OTP login (backend sends a 6-digit code to the admin's
    // email at login time; no tokens are issued until this is verified).
    async mfaEmailVerify(email, code) { return this.request("/auth/mfa-email-verify", { method: "POST", body: JSON.stringify({ email, code }) }); }

    // Products
    async getProducts(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/products${query ? `?${query}` : ""}`);
    }
    async getProduct(idOrSlug) { return this.request(`/products/${idOrSlug}`); }

    // Cart
    async getCart() { return this.request("/cart"); }
    async addToCart(productId, quantity = 1, variantId = null) {
        return this.request("/cart/items", {
            method: "POST",
            body: JSON.stringify({ product_id: productId, quantity, variant_id: variantId }),
        });
    }
    async updateCartItem(itemId, quantity) {
        return this.request(`/cart/items/${itemId}`, {
            method: "PATCH",
            body: JSON.stringify({ quantity }),
        });
    }
    async removeCartItem(itemId) {
        return this.request(`/cart/items/${itemId}`, { method: "DELETE" });
    }
    async clearCart() { return this.request("/cart/clear", { method: "DELETE" }); }

    // Checkout
    async createCheckout(data) { return this.request("/checkout", { method: "POST", body: JSON.stringify(data) }); }
    async getCheckoutSession() { return this.request("/checkout/session"); }

    // Payments
    async getPaymentConfig() { return this.request("/payments/config"); }
    async initializePayment(orderId) { return this.request(`/payments/initialize/${orderId}`, { method: "POST" }); }
    async paymentCallback(params) { return this.request(`/payments/callback?${new URLSearchParams(params).toString()}`); }
    async verifyPayment(reference) { return this.request(`/payments/verify/${reference}`); }

    // Orders
    async getOrders(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/orders${query ? `?${query}` : ""}`);
    }
    async getOrder(id) { return this.request(`/orders/${id}`); }

    // Admin
    // Suppliers
    async getSuppliers(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/admin/suppliers${query ? `?${query}` : ""}`);
    }
    async createSupplier(data) { return this.request("/admin/suppliers", { method: "POST", body: JSON.stringify(data) }); }
    async getSupplier(id) { return this.request(`/admin/suppliers/${id}`); }
    async updateSupplier(id, data) { return this.request(`/admin/suppliers/${id}`, { method: "PUT", body: JSON.stringify(data) }); }
    async deleteSupplier(id) { return this.request(`/admin/suppliers/${id}`, { method: "DELETE" }); }

    async getAdminStats() { return this.request("/admin/dashboard"); }
    async getAdminProducts(params = {}) {
        // Filter out undefined/null values BEFORE serializing  -  otherwise
        // URLSearchParams would convert them to the string "undefined",
        // which the backend would treat as a literal search term and return
        // an empty list (e.g. ?q=undefined matches nothing).
        const clean = {};
        for (const k in params) {
            const v = params[k];
            if (v !== undefined && v !== null && v !== "") {
                clean[k] = v;
            }
        }
        const query = new URLSearchParams(clean).toString();
        return this.request(`/admin/products${query ? `?${query}` : ""}`);
    }
    async getAdminProduct(id) { return this.request(`/admin/products/${id}`); }
    async createProduct(data) { return this.request("/admin/products", { method: "POST", body: JSON.stringify(data) }); }
    async updateProduct(id, data) { return this.request(`/admin/products/${id}`, { method: "PUT", body: JSON.stringify(data) }); }
    async deleteProduct(id) { return this.request(`/admin/products/${id}`, { method: "DELETE" }); }
    async getCategories() { return this.request("/admin/categories"); }

    // Image upload (multipart/form-data)  -  sends to backend, returns {url, filename}
    async uploadImage(file) {
        const form = new FormData();
        form.append("file", file);
        const response = await fetch(`${this.baseUrl}/admin/upload/image`, {
            method: "POST",
            headers: {
                "X-Request-ID": this.generateRequestId(),
                "X-CSRFToken": this.getCsrfToken() || undefined,
            },
            body: form,
            credentials: "include",
        });
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            const err = new Error(data.detail || "Upload failed");
            err.status = response.status;
            throw err;
        }
        return response.json();
    }
    async getAdminOrders(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/admin/orders${query ? `?${query}` : ""}`);
    }
    async updateOrderStatus(id, status) {
        return this.request(`/admin/orders/${id}/status`, { method: "PUT", body: JSON.stringify({ status }) });
    }
    async getAdminUsers(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/admin/users${query ? `?${query}` : ""}`);
    }
    async getAuditLogs(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/admin/audit-logs${query ? `?${query}` : ""}`);
    }
}

window.api = new ApiClient();

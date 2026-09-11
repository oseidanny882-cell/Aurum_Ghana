/*
 * Aurum Ghana - Admin Module
 * Admin dashboard logic
 */

const Admin = {
    async init() {
        // CRITICAL: wait for Auth.init() to finish before checking admin status.
        // Auth.init() loads user from localStorage and verifies the token against
        // the backend. Without this await, redirectIfNotAdmin() can run before
        // Auth.user is populated (or after a failed verify cleared it), causing
        // a logged-in admin to be redirected back to the home page -- especially
        // when navigating via the browser back button.
        await Auth.init();
        if (!Auth.redirectIfNotAdmin()) return;
        await this.loadDashboard();
        this.setupNavigation();
    },

    async loadDashboard() {
        const statsEl = document.getElementById("stats-grid");
        if (!statsEl) return;
        try {
            const stats = await window.api.getAdminStats();
            statsEl.innerHTML = `
                <div class="stat-card"><p class="stat-label">Revenue</p><p class="stat-value">${Products.formatPrice(stats.revenue)}</p><p class="stat-change ${stats.revenue_change >= 0 ? "up" : "down"}">${stats.revenue_change >= 0 ? "+" : ""}${stats.revenue_change}% vs last month</p></div>
                <div class="stat-card"><p class="stat-label">Orders</p><p class="stat-value">${stats.orders}</p><p class="stat-change ${stats.orders_change >= 0 ? "up" : "down"}">${stats.orders_change >= 0 ? "+" : ""}${stats.orders_change}% vs last month</p></div>
                <div class="stat-card"><p class="stat-label">Customers</p><p class="stat-value">${stats.customers}</p><p class="stat-change ${stats.customers_change >= 0 ? "up" : "down"}">${stats.customers_change >= 0 ? "+" : ""}${stats.customers_change}% vs last month</p></div>
                <div class="stat-card"><p class="stat-label">Conversion Rate</p><p class="stat-value">${stats.conversion_rate}%</p><p class="stat-change ${stats.conversion_change >= 0 ? "up" : "down"}">${stats.conversion_change >= 0 ? "+" : ""}${stats.conversion_change}% vs last month</p></div>
            `;
        } catch (e) {
            statsEl.innerHTML = `<p class="text-muted">Failed to load stats. Backend not available.</p>`;
        }
    },

    setupNavigation() {
        // Highlight active nav item
        const path = window.location.pathname;
        document.querySelectorAll(".admin-nav a").forEach(link => {
            if (link.getAttribute("href") && path.includes(link.getAttribute("href"))) {
                link.classList.add("active");
            }
        });
    },
};

window.Admin = Admin;

/**
 * Aurum Ghana - Admin Orders Module
 * Lists orders with pagination and status update
 */

const AdminOrders = {
    STATUSES: ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "refunded"],

    init() {
        Auth.init().then(() => {
            if (!Auth.redirectIfNotAdmin()) return;
            this.loadOrders();
        });
    },

    statusBadge(status) {
        const map = {
            pending: "status-pending",
            confirmed: "status-paid",
            processing: "status-shipped",
            shipped: "status-shipped",
            delivered: "status-delivered",
            cancelled: "status-cancelled",
            refunded: "status-refunded",
        };
        const cls = map[status] || "status-pending";
        const label = status ? status.charAt(0).toUpperCase() + status.slice(1) : " - ";
        return `<span class="status-badge ${cls}">${label}</span>`;
    },

    async loadOrders(page = 1) {
        const el = document.getElementById("orders-table");
        if (!el) return;
        el.innerHTML = '<p style="padding:1rem;text-align:center;color:var(--color-text-muted);">Loading orders…</p>';

        try {
            const data = await window.api.getAdminOrders({ page, per_page: 20 });
            const { items = [], total = 0, per_page = 20 } = data;
            const pages = Math.ceil(total / per_page) || 1;

            if (items.length === 0) {
                el.innerHTML = emptyTable();
                return;
            }

            const rows = items.map(o => this.renderRow(o)).join("");
            let pagination = "";
            if (pages > 1) pagination = this.renderPagination(page, pages, total);
            el.innerHTML = wrapTable(rows) + pagination;
        } catch (err) {
            el.innerHTML = `<p style="padding:1rem;color:var(--color-error);">Failed to load orders: ${window.Security.escapeHtml(err.message || "Backend not available.")}</p>`;
        }
    },

    renderRow(o) {
        const esc = window.Security.escapeHtml;
        const num = o.order_number || (o.id ? o.id.slice(0, 8) : " - ");
        const name = esc(o.user_name || o.user_email || " - ");
        const email = esc(o.user_email || " - ");
        const total = window.Products.formatPrice(o.total);
        const date = o.created_at
            ? new Date(o.created_at).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" })
            : " - ";
        const opts = this.STATUSES.map(s =>
            `<option value="${s}"${s === o.status ? " selected" : ""}>${s.charAt(0).toUpperCase() + s.slice(1)}</option>`
        ).join("");
        return `<tr data-id="${esc(o.id)}">
            <td><strong>#${esc(num)}</strong></td>
            <td><strong>${name}</strong><br><small style="color:var(--color-text-muted)">${email}</small></td>
            <td>${total}</td>
            <td>${this.statusBadge(o.status)}</td>
            <td>${date}</td>
            <td>
                <select onchange="AdminOrders.updateStatus('${esc(o.id)}', this.value)"
                    style="padding:4px 8px;border-radius:4px;border:1px solid var(--color-border);font-size:0.875rem;cursor:pointer;">
                    ${opts}
                </select>
            </td>
        </tr>`;
    },

    renderPagination(page, pages, total) {
        const prevDisabled = page <= 1;
        const nextDisabled = page >= pages;
        return `<div style="padding:1rem;display:flex;justify-content:center;gap:8px;flex-wrap:wrap;align-items:center;">
            <button onclick="AdminOrders.loadOrders(${page - 1})"${prevDisabled ? " disabled" : ""}
                style="padding:6px 14px;cursor:${prevDisabled ? "not-allowed" : "pointer"};opacity:${prevDisabled ? "0.4" : "1"};">
                &laquo; Prev
            </button>
            <span style="padding:6px 12px;">Page ${page} of ${pages} &nbsp;·&nbsp; ${total} orders</span>
            <button onclick="AdminOrders.loadOrders(${page + 1})"${nextDisabled ? " disabled" : ""}
                style="padding:6px 14px;cursor:${nextDisabled ? "not-allowed" : "pointer"};opacity:${nextDisabled ? "0.4" : "1"};">
                Next &raquo;
            </button>
        </div>`;
    },

    async updateStatus(orderId, newStatus) {
        try {
            await window.api.updateOrderStatus(orderId, newStatus);
            this.showToast(`Order status updated to "${newStatus}"`, "success");
            this.loadOrders();
        } catch (err) {
            this.showToast(`Failed to update: ${err.message || "Server error"}`, "error");
            this.loadOrders();
        }
    },

    showToast(msg, type = "info") {
        const c = document.getElementById("toast-container");
        if (!c) return;
        const el = document.createElement("div");
        el.className = `toast toast-${type}`;
        el.textContent = msg;
        c.appendChild(el);
        setTimeout(() => el.remove(), 4000);
    },
};

function wrapTable(rows) {
    return `<div class="admin-table-wrap">
        <table class="admin-table">
            <thead>
                <tr>
                    <th>Order #</th><th>Customer</th><th>Total</th>
                    <th>Status</th><th>Date</th><th>Actions</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    </div>`;
}

function emptyTable() {
    return wrapTable('<tr><td colspan="6" style="text-align:center;padding:2rem;color:var(--color-text-muted);">No orders found.</td></tr>');
}

window.AdminOrders = AdminOrders;

// Auto-init
document.addEventListener("DOMContentLoaded", () => AdminOrders.init());

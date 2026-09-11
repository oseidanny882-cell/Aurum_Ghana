/**
 * Aurum Ghana - Admin Users Module
 * Lists users with pagination and status toggle
 */

const AdminUsers = {
    init() {
        Auth.init().then(() => {
            if (!Auth.redirectIfNotAdmin()) return;
            this.loadUsers();
        });
    },

    roleBadge(role) {
        const map = {
            admin: "status-admin",
            user: "status-user",
            vendor: "status-vendor",
            staff: "status-staff",
        };
        const cls = map[role] || "status-user";
        const label = role ? role.charAt(0).toUpperCase() + role.slice(1) : "User";
        return `<span class="status-badge ${cls}">${label}</span>`;
    },

    verifiedBadge(verified) {
        if (verified) {
            return `<span class="status-badge" style="background:#e8f5e9;color:#2e7d32;font-size:11px;">Verified</span>`;
        }
        return `<span class="status-badge" style="background:#fff3e0;color:#e65100;font-size:11px;">Unverified</span>`;
    },

    activeBadge(active) {
        if (active) {
            return `<span class="status-badge status-active">Active</span>`;
        }
        return `<span class="status-badge status-inactive">Inactive</span>`;
    },

    async loadUsers(page = 1) {
        const el = document.getElementById("users-table");
        if (!el) return;
        el.innerHTML = '<p style="padding:20px;text-align:center;color:#888;">Loading users...</p>';

        try {
            const data = await window.api.getAdminUsers({ page, per_page: 20 });
            const items = data.items || [];
            const total = data.total || 0;
            const per_page = data.per_page || 20;
            const pages = Math.ceil(total / per_page) || 1;

            if (items.length === 0) {
                el.innerHTML = emptyTable();
                return;
            }

            const rows = items.map(u => this.renderRow(u)).join("");
            let pagination = "";
            if (pages > 1) pagination = this.renderPagination(page, pages, total);

            el.innerHTML = wrapTable(rows) + pagination;
        } catch (err) {
            el.innerHTML = `<p style="padding:20px;color:#c62828;">Failed to load users: ${window.Security.escapeHtml(err.message || "Backend not available.")}</p>`;
        }
    },

    renderRow(u) {
        const esc = this.esc;
        const name = esc(u.name || (u.email ? u.email.split("@")[0] : " - "));
        const email = esc(u.email || " - ");
        const date = u.created_at
            ? new Date(u.created_at).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" })
            : " - ";

        return `<tr style="border-bottom:1px solid #f0f0f0;">
            <td style="padding:10px 8px;">
                <strong>${name}</strong>
            </td>
            <td style="padding:10px 8px;color:#555;">${email}</td>
            <td style="padding:10px 8px;">${this.roleBadge(u.role)}</td>
            <td style="padding:10px 8px;">${this.verifiedBadge(u.is_verified)}</td>
            <td style="padding:10px 8px;">${this.activeBadge(u.is_active)}</td>
            <td style="padding:10px 8px;color:#888;font-size:13px;">${date}</td>
        </tr>`;
    },

    renderPagination(page, pages, total) {
        const prevDisabled = page <= 1;
        const nextDisabled = page >= pages;
        return `<div style="padding:16px;display:flex;justify-content:center;gap:8px;flex-wrap:wrap;align-items:center;">
            <button onclick="AdminUsers.loadUsers(${page - 1})"${prevDisabled ? " disabled" : ""}
                style="padding:6px 12px;cursor:${prevDisabled ? "not-allowed" : "pointer"};opacity:${prevDisabled ? "0.4" : "1"};">
                &laquo; Prev
            </button>
            <span style="padding:6px 12px;">Page ${page} of ${pages} &nbsp;&middot;&nbsp; ${total} users</span>
            <button onclick="AdminUsers.loadUsers(${page + 1})"${nextDisabled ? " disabled" : ""}
                style="padding:6px 12px;cursor:${nextDisabled ? "not-allowed" : "pointer"};opacity:${nextDisabled ? "0.4" : "1"};">
                Next &raquo;
            </button>
        </div>`;
    },

    esc(s) {
        if (!s) return "";
        return String(s)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    },
};

function wrapTable(rows) {
    return `<div class="admin-table-wrap">
        <table class="admin-table">
            <thead>
                <tr style="border-bottom:2px solid #eee;text-align:left;">
                    <th style="padding:12px 8px;">Name</th>
                    <th style="padding:12px 8px;">Email</th>
                    <th style="padding:12px 8px;">Role</th>
                    <th style="padding:12px 8px;">Verified</th>
                    <th style="padding:12px 8px;">Status</th>
                    <th style="padding:12px 8px;">Joined</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    </div>`;
}

function emptyTable() {
    return wrapTable('<tr><td colspan="6" style="text-align:center;padding:2rem;color:#888;">No users found.</td></tr>');
}

window.AdminUsers = AdminUsers;
document.addEventListener("DOMContentLoaded", () => AdminUsers.init());

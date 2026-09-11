/*
 * Aurum Ghana - Auth Module
 * Authentication state and helpers
 *
 * Security notes:
 * - JWT access/refresh tokens live in HttpOnly, SameSite cookies set by the
 *   backend (see backend/api/auth.py). This means they are NOT readable by
 *   JavaScript, which protects against XSS-based token theft.
 * - Plaintext passwords NEVER touch any storage layer; they live only in the
 *   <input type="password"> while the user is typing and are sent immediately
 *   to the backend over HTTPS.
 * - Login button disable prevents double-submit / brute-force from the UI.
 * - User profile data is kept in sessionStorage for UI state only  -  it is not
 *   used as a credential and is cleared on tab close.
 */

const Auth = {
    isAuthenticated: false,
    // Set when a login succeeded but MFA verification is still required
    // (role=admin + ADMIN_MFA_REQUIRED). Until this is cleared via
    // completeMfaLogin(), the stored JWT cannot access admin routes.
    mfaPending: false,
    // sessionStorage-backed token storage (wiped on tab close).
    _store(key, val) { try { sessionStorage.setItem(key, val); } catch (e) {} },
    _load(key) { try { return sessionStorage.getItem(key); } catch (e) { return null; } },
    _remove(key) { try { sessionStorage.removeItem(key); } catch (e) {} },

    user: null,

    async init() {
        const cached = this._load("user");
        // Restore pending-MFA flag if present
        this.mfaPending = this._load("mfa_pending") === "1";

        // If MFA is still pending, always restore the cached user object so the
        // emailed-code step can read this.user.email to complete the login.
        if (this.mfaPending && cached) {
            try {
                this.user = JSON.parse(cached);
                this.isAuthenticated = true;
                return;
            } catch { this.logout(); return; }
        }

        if (cached) {
            try {
                this.user = JSON.parse(cached);
                this.isAuthenticated = true;
                if (this.mfaPending) return;
                // Verify token validity in background
                try {
                    await this.getProfile();
                } catch {
                    this.user = null;
                    this.isAuthenticated = false;
                    this._remove("user");
                }
            } catch { this.logout(); }
        }
    },

    async login(email, password) {
        const res = await window.api.login(email, password);
        this.mfaPending = res.mfa_required === true;
        this.mfaSetupPended = res.mfa_setup_required === true;
        if (res.user) this._store("user", JSON.stringify(res.user));
        this.user = res.user;
        this.isAuthenticated = true;
        if (this.mfaPending) this._store("mfa_pending", "1"); else this._remove("mfa_pending");
        return res;
    },

    async completeMfaLogin(code) {
        const email = this.user && this.user.email;
        if (!email) throw new Error("Session expired. Please sign in again.");
        const res = await window.api.mfaEmailVerify(email, code);
        if (res.user) this._store("user", JSON.stringify(res.user));
        this.user = res.user || this.user;
        this.isAuthenticated = true;
        this.mfaPending = false;
        this._remove("mfa_pending");
        return res;
    },

    async register(data) {
        const res = await window.api.register(data);
        if (res.user) this._store("user", JSON.stringify(res.user));
        this.user = res.user;
        this.isAuthenticated = true;
        return res;
    },

    async logout() {
        await window.api.logout();
        this.user = null;
        this.isAuthenticated = false;
        this.mfaPending = false;
        // Clear local cart on logout
        if (window.Cart) {
            window.Cart.clear();
        }
        this._remove("user");
        this._remove("mfa_pending");
    },

    async getProfile() {
        const res = await window.api.getProfile();
        this.user = res;
        this._store("user", JSON.stringify(res));
        return res;
    },

    isAdmin() {
        if (!this.user) return false;
        return ["admin", "super_admin"].includes(this.user.role);
    },

    // True when the current session is allowed to see admin content (MFA done).
    isAdminReady() {
        return this.isAdmin() && !this.mfaPending;
    },

    redirectIfAuthed(target = "/account.html") {
        if (this.isAuthenticated) window.location.href = target;
    },

    redirectIfNotAuthed(target = "/login.html") {
        if (!this.isAuthenticated) {
            window.location.href = target;
            return false;
        }
        return true;
    },

    redirectIfNotAdmin(target = "/") {
        if (!this.isAdminReady()) {
            window.location.href = (this.isAdmin() && this.mfaPending) ? "/login.html" : target;
            return false;
        }
        return true;
    },
};

window.Auth = Auth;

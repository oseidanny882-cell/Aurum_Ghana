/*

 * Aurum Ghana - Frontend Security Utilities

 * Sanitization, validation, and security helpers

 */



(function() {

    "use strict";



    const Security = {

        // Escape HTML to prevent XSS

        escapeHtml(text) {

            if (text === null || text === undefined) return "";

            const div = document.createElement("div");

            div.textContent = String(text);

            return div.innerHTML;

        },



        // Sanitize URL to prevent javascript: and data: XSS

        sanitizeUrl(url) {

            if (typeof url !== "string") return "";

            const cleaned = url.trim();

            if (/^(javascript|data|vbscript):/i.test(cleaned)) return "";

            if (cleaned.startsWith("/") || cleaned.startsWith("http://") || cleaned.startsWith("https://")) {

                return cleaned;

            }

            return "";

        },



        // Email validation

        isValidEmail(email) {

            const re = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;

            return re.test(String(email).trim());

        },



        // Ghana phone validation (e.g., 0241234567, +233241234567)

        isValidGhanaPhone(phone) {

            const cleaned = String(phone).replace(/[\s\-\(\)]/g, "");

            return /^(\+?233|0)?[2-9][0-9]{8}$/.test(cleaned);

        },



        // Password strength (8+, upper, lower, number, special)

        passwordStrength(password) {

            if (typeof password !== "string") return { score: 0, valid: false };

            let score = 0;

            if (password.length >= 8) score++;

            if (password.length >= 12) score++;

            if (/[a-z]/.test(password)) score++;

            if (/[A-Z]/.test(password)) score++;

            if (/[0-9]/.test(password)) score++;

            if (/[^A-Za-z0-9]/.test(password)) score++;

            return { score, valid: password.length >= 8 && score >= 4 };

        },



        // CSRF token retrieval

        getCsrfToken() {

            const match = document.cookie.match(/csrftoken=([^;]+)/);

            return match ? match[1] : null;

        },




        // Login attempt limiter (client-side, best-effort - server is authoritative).
        // Tracks failed attempts per email in-memory so a page refresh resets the
        // counter (we don't want to lock out honest users who reload to recover).
        _loginAttempts: new Map(),
        checkLoginAllowed(email) {
            const key = (email || "").toLowerCase();
            const now = Date.now();
            const rec = this._loginAttempts.get(key);
            if (rec && rec.lockedUntil > now) {
                const secs = Math.ceil((rec.lockedUntil - now) / 1000);
                return { allowed: false, retryAfterSec: secs, attempts: rec.count };
            }
            if (rec && rec.lockedUntil && rec.lockedUntil <= now) {
                this._loginAttempts.delete(key);
            }
            return { allowed: true, attempts: rec ? rec.count : 0 };
        },
        recordLoginFailure(email) {
            const key = (email || "").toLowerCase();
            const now = Date.now();
            const rec = this._loginAttempts.get(key) || { count: 0, lockedUntil: 0 };
            rec.count++;
            if (rec.count >= 5) {
                // Exponential backoff: 1 min after 5 fails, 2 min after 6, etc.
                const minutes = Math.min(15, Math.pow(2, rec.count - 5));
                rec.lockedUntil = now + minutes * 60 * 1000;
            }
            this._loginAttempts.set(key, rec);
            return rec;
        },
        recordLoginSuccess(email) {
            this._loginAttempts.delete((email || "").toLowerCase());
        },

        // Content Security Policy helpers - set meta tag if needed

        applyCSP() {

            if (!document.querySelector("meta[http-equiv=Content-Security-Policy]")) {

                const meta = document.createElement("meta");

                meta.httpEquiv = "Content-Security-Policy";

                meta.content = `default-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com; img-src 'self' data: https:; script-src 'self' 'unsafe-inline' https://js.paystack.co; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; connect-src 'self' https://api.paystack.co https://web-production-b4e16.up.railway.app http://127.0.0.1:5000 http://localhost:5000; frame-src https://checkout.paystack.com;`;

                document.head.appendChild(meta);

            }

        },



        // Rate limiter for client-side (best effort, server is authoritative)

        rateLimit(key, max = 5, windowMs = 60000) {

            try {

                const now = Date.now();

                const stored = JSON.parse(localStorage.getItem(`rl_${key}`) || "{}");

                if (stored.reset && stored.reset < now) {

                    localStorage.removeItem(`rl_${key}`);

                    stored.count = 0;

                    stored.reset = now + windowMs;

                }

                if (!stored.reset) stored.reset = now + windowMs;

                if (!stored.count) stored.count = 0;

                stored.count++;

                localStorage.setItem(`rl_${key}`, JSON.stringify(stored));

                return stored.count <= max;

            } catch {

                return true;

            }

        },



        // Sanitize form input on the fly

        sanitizeInput(str) {

            if (str === null || str === undefined) return "";

            return String(str).replace(/[<>]/g, "");

        },



        // Logout and clear all sensitive data

        clearSensitiveData() {

            // Wipe both storage backends  -  auth module now prefers

            // sessionStorage, but legacy code may still write to localStorage.

            try {

                localStorage.removeItem("access_token");

                localStorage.removeItem("refresh_token");

                localStorage.removeItem("user");

                localStorage.removeItem("csrf_token");

                sessionStorage.removeItem("access_token");

                sessionStorage.removeItem("refresh_token");

                sessionStorage.removeItem("user");

                sessionStorage.removeItem("csrf_token");

            } catch (e) {}

        },



        // Detect if running in a secure context

        isSecureContext() {

            return window.isSecureContext || window.location.protocol === "https:";

        },

    };



    window.Security = Security;

    document.addEventListener("DOMContentLoaded", () => Security.applyCSP());

})();


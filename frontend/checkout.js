/*
 * Aurum Ghana - Checkout Module
 * Checkout form handling and Paystack integration
 */

const Checkout = {
    async init() {
        this.renderSummary();
        this.setupForm();
        this.populateAddress();
        // If the user is not logged in, show a prompt and gate the page.
        // Cart is preserved in localStorage so items are not lost on the way to login.
        if (!window.Auth?.isAuthenticated) {
            this.showLoginRequiredPrompt();
        }
    },

    showLoginRequiredPrompt() {
        // Overlay that covers the checkout form so the user cannot submit
        // until they sign in. Cart items are kept so the flow resumes after login.
        const existing = document.getElementById("login-required-overlay");
        if (existing) return;
        const overlay = document.createElement("div");
        overlay.id = "login-required-overlay";
        overlay.setAttribute("role", "dialog");
        overlay.setAttribute("aria-modal", "true");
        overlay.setAttribute("aria-labelledby", "login-required-title");
        overlay.innerHTML = `
            <style>
                #login-required-overlay {
                    position: fixed; inset: 0; z-index: 1000;
                    background: rgba(20, 18, 14, 0.55);
                    backdrop-filter: blur(2px);
                    display: flex; align-items: center; justify-content: center;
                    padding: 1rem;
                }
                #login-required-overlay .prompt-card {
                    background: #fff; border-radius: 12px;
                    max-width: 440px; width: 100%;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.25);
                    padding: 2rem; text-align: center;
                    font-family: 'Inter', system-ui, sans-serif;
                }
                #login-required-overlay .prompt-icon {
                    width: 56px; height: 56px; margin: 0 auto 1rem;
                    border-radius: 50%;
                    background: #f6f1ea;
                    display: flex; align-items: center; justify-content: center;
                }
                #login-required-overlay .prompt-icon svg {
                    width: 28px; height: 28px; color: #c8a96a;
                }
                #login-required-overlay h2 {
                    font-family: 'Cormorant Garamond', serif;
                    font-size: 1.75rem; margin: 0 0 0.5rem;
                    color: #1a1a1a; font-weight: 600;
                }
                #login-required-overlay p {
                    color: #6b5b3a; line-height: 1.55;
                    margin: 0 0 1.5rem; font-size: 0.95rem;
                }
                #login-required-overlay .prompt-actions {
                    display: flex; gap: 0.75rem; justify-content: center;
                    flex-wrap: wrap;
                }
                #login-required-overlay .btn {
                    display: inline-block; padding: 0.75rem 1.5rem;
                    border-radius: 6px; text-decoration: none;
                    font-weight: 500; font-size: 0.95rem;
                    border: none; cursor: pointer; font-family: inherit;
                    transition: transform 0.15s, background 0.15s;
                }
                #login-required-overlay .btn-primary {
                    background: #c8a96a; color: #fff;
                }
                #login-required-overlay .btn-primary:hover { background: #b89a5e; }
                #login-required-overlay .btn-ghost {
                    background: transparent; color: #1a1a1a;
                    border: 1px solid #d8d0c0;
                }
                #login-required-overlay .btn-ghost:hover { background: #f6f1ea; }
                #login-required-overlay .prompt-note {
                    margin-top: 1.25rem; font-size: 0.8rem;
                    color: #999; line-height: 1.4;
                }
            </style>
            <div class="prompt-card">
                <div class="prompt-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                        <circle cx="12" cy="7" r="4"/>
                    </svg>
                </div>
                <h2 id="login-required-title">Please log in to continue</h2>
                <p>You need an account to complete your checkout. Your cart items will be saved and waiting for you when you return.</p>
                <div class="prompt-actions">
                    <a href="login.html?redirect=checkout.html" class="btn btn-primary" id="prompt-login-btn">Log in</a>
                    <a href="register.html?redirect=checkout.html" class="btn btn-ghost" id="prompt-register-btn">Create account</a>
                </div>
                <p class="prompt-note">Already have an account? Click <strong>Log in</strong> above to continue.</p>
            </div>
        `;
        document.body.appendChild(overlay);
        // Also disable the submit button as a belt-and-suspenders fallback.
        const btn = document.getElementById("checkout-submit");
        if (btn) {
            btn.disabled = true;
            btn.title = "Please log in to proceed with checkout";
            btn.style.opacity = "0.5";
            btn.style.cursor = "not-allowed";
        }
    },

    renderSummary() {
        const el = document.getElementById("checkout-summary");
        if (!el) return;
        const cart = window.Cart;
        el.innerHTML = `
            <h2>Order summary</h2>
            ${cart.items.map(item => `
                <div class="cart-line">
                    <span>${window.Security.escapeHtml(item.name)} x${item.quantity}</span>
                    <span>${window.Products.formatPrice((item.discount_price || item.price) * item.quantity)}</span>
                </div>
            `).join("")}
            <div class="cart-line"><span>Subtotal</span><span>${window.Products.formatPrice(cart.subtotal)}</span></div>
            <div class="cart-line"><span>Delivery</span><span>${cart.delivery_fee === 0 ? "Free" : window.Products.formatPrice(cart.delivery_fee)}</span></div>
            ${cart.discount > 0 ? `<div class="cart-line"><span>Discount</span><span>-${window.Products.formatPrice(cart.discount)}</span></div>` : ""}
            <div class="cart-line total"><span>Total</span><span>${window.Products.formatPrice(cart.total)}</span></div>
        `;
    },

    setupForm() {
        const form = document.getElementById("checkout-form");
        if (!form) return;
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (!this.validateForm()) return;
            await this.submit();
        });
    },

    validateForm() {
        // Map the IDs to the actual elements in checkout.html.
        // Form uses single "full_name" input; the backend expects first_name + last_name.
        const fields = ["full_name", "email", "phone", "address", "city", "region"];
        let valid = true;
        for (const id of fields) {
            const el = document.getElementById(id);
            if (!el) continue; // skip if element not present on this page variant
            if (!el.value.trim()) {
                el.classList.add("error");
                valid = false;
            } else {
                el.classList.remove("error");
            }
        }
        // Validate Ghana phone
        const phoneEl = document.getElementById("phone");
        if (phoneEl && phoneEl.value && !window.Security.isValidGhanaPhone(phoneEl.value)) {
            phoneEl.classList.add("error");
            showToast("Please enter a valid Ghana phone number", "error");
            valid = false;
        }
        const emailEl = document.getElementById("email");
        if (emailEl && emailEl.value && !window.Security.isValidEmail(emailEl.value)) {
            emailEl.classList.add("error");
            showToast("Please enter a valid email address", "error");
            valid = false;
        }
        return valid;
    },

    populateAddress() {
        // Pre-fill from saved address if available
        const saved = localStorage.getItem("checkout_address");
        if (saved) {
            try {
                const addr = JSON.parse(saved);
                Object.keys(addr).forEach(key => {
                    const el = document.getElementById(key);
                    if (el) el.value = addr[key];
                });
            } catch {}
        }
    },

    async submit() {
        // Defense in depth: also gate at submit time
        if (!window.Auth?.isAuthenticated) {
            this.showLoginRequiredPrompt();
            return;
        }
        const btn = document.getElementById("checkout-submit");
        if (btn) { btn.disabled = true; btn.innerHTML = "<span class=loading-spinner></span> Processing..."; }
        try {
            const val = (id) => (document.getElementById(id)?.value || "").trim();
            const fullName = val("full_name");
            const nameParts = fullName.split(/\s+/).filter(Boolean);
            const firstName = nameParts[0] || "";
            const lastName  = nameParts.slice(1).join(" ") || firstName;
            const formData = {
                first_name:  firstName,
                last_name:   lastName,
                email:       val("email"),
                phone:       val("phone"),
                street:      val("address"),
                city:        val("city"),
                region:      val("region") || "Greater Accra",
                delivery_notes: val("instructions"),
                country:     "Ghana",
            };
            // Save for next time
            localStorage.setItem("checkout_address", JSON.stringify(formData));
            // Create checkout session
            const checkout = await window.api.createCheckout({
                ...formData,
                items: window.Cart.items,
            });
            if (checkout.order_id) {
                // Initialize Paystack payment
                const payment = await window.api.initializePayment(checkout.order_id);
                if (payment.authorization_url) {
                    // Redirect to Paystack
                    window.location.href = payment.authorization_url;
                } else {
                    throw new Error("Payment initialization failed");
                }
            }
        } catch (err) {
            showToast(err.message || "Checkout failed. Please try again.", "error");
        } finally {
            if (btn) { btn.disabled = false; btn.textContent = "Continue to payment"; }
        }
    },
};

window.Checkout = Checkout;

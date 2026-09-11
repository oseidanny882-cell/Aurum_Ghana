(function() {

    'use strict';



    // ─── Password strength meter ─────────────────────────────────────────────

    (function() {

        var passwordInput = document.getElementById('password');

        var strengthDiv   = document.getElementById('password-strength');

        if (!passwordInput || !strengthDiv) return;

        var LEVELS = [

            { label: 'Too short',  color: '#e74c3c', width: '20%' },

            { label: 'Weak',        color: '#e67e22', width: '40%' },

            { label: 'Fair',        color: '#f39c12', width: '60%' },

            { label: 'Strong',      color: '#27ae60', width: '80%' },

            { label: 'Very strong', color: '#1e8449', width: '100%' },

        ];

        function score(pw) {

            if (!pw || pw.length < 4) return -1;

            var s = 0;

            if (pw.length >= 8)  s++;

            if (pw.length >= 12) s++;

            if (/[A-Z]/.test(pw)) s++;

            if (/[a-z]/.test(pw)) s++;

            if (/[0-9]/.test(pw)) s++;

            if (/[^A-Za-z0-9]/.test(pw)) s++;

            return Math.min(Math.max(s - 1, 0), 4);

        }

        passwordInput.addEventListener('input', function() {

            var lvl = score(passwordInput.value);

            if (lvl < 0) { strengthDiv.innerHTML = ''; return; }

            var level = LEVELS[lvl];

            strengthDiv.innerHTML = '<div style="height:3px;border-radius:2px;background:#eee;overflow:hidden;margin-bottom:3px;"><div style="height:100%;width:' + level.width + ';background:' + level.color + ';transition:width 0.25s,background 0.25s;"></div></div><span style="font-size:0.75rem;color:' + level.color + ';">' + level.label + '</span>';

        });

    })();



    // Login Form

    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submit  = document.getElementById('login-submit');
            const alertEl = document.getElementById('login-alert');
            if (alertEl) { alertEl.style.display = 'none'; }
            const email    = loginForm.email.value.trim();
            const password = loginForm.password.value;

            if (!window.Security.isValidEmail(email)) {
                if (alertEl) { alertEl.textContent = 'Please enter a valid email address.'; alertEl.className = 'alert alert-error'; alertEl.style.display = 'block'; }
                return;
            }
            if (password.length < 6) {
                if (alertEl) { alertEl.textContent = 'Password must be at least 6 characters.'; alertEl.className = 'alert alert-error'; alertEl.style.display = 'block'; }
                return;
            }

            // Client-side rate limit (best-effort; backend is authoritative)
            const check = window.Security.checkLoginAllowed(email);
            if (!check.allowed) {
                const mins = Math.ceil(check.retryAfterSec / 60);
                const msg  = mins >= 1
                    ? 'Too many failed attempts. Please wait ' + mins + ' minute(s) before trying again.'
                    : 'Too many failed attempts. Please wait ' + check.retryAfterSec + ' second(s) before trying again.';
                if (alertEl) { alertEl.textContent = msg; alertEl.className = 'alert alert-error'; alertEl.style.display = 'block'; }
                return;
            }

            submit.disabled = true;
            submit.textContent = 'Signing in...';
            try {
                await window.Auth.login(email, password);
                window.Security.recordLoginSuccess(email);
                if (window.initAuthState) window.initAuthState();
                // Admins must complete the login-time MFA step first.
                if (window.Auth.mfaPending) {
                    window.location.href = 'mfa.html';
                } else {
                    const redirect = new URLSearchParams(window.location.search).get('redirect');
                    window.location.href = redirect || (window.Auth.isAdmin() ? 'admin-products.html' : 'account.html');
                }
            } catch (err) {
                window.Security.recordLoginFailure(email);
                if (err.code === 'account_locked' || err.status === 429) {
                    if (alertEl) { alertEl.textContent = err.message || 'Account temporarily locked. Please wait before trying again.'; alertEl.className = 'alert alert-error'; alertEl.style.display = 'block'; }
                    submit.textContent = 'Locked';
                    let secs = 60;
                    const tick = setInterval(() => {
                        secs--;
                        if (secs <= 0) { clearInterval(tick); submit.disabled = false; submit.textContent = 'Sign in'; }
                        else { submit.textContent = 'Try again in ' + secs + 's'; }
                    }, 1000);
                } else if (err.status === 401 || err.code === 'invalid_credentials') {
                    if (alertEl) { alertEl.textContent = 'Invalid email or password.'; alertEl.className = 'alert alert-error'; alertEl.style.display = 'block'; }
                } else {
                    if (alertEl) { alertEl.textContent = err.message || 'Sign in failed. Please try again.'; alertEl.className = 'alert alert-error'; alertEl.style.display = 'block'; }
                }
            } finally {
                if (!submit.disabled) { submit.disabled = false; submit.textContent = 'Sign in'; }
            }
        });
    }

    // Register Form

    const registerForm = document.getElementById('register-form');

    if (registerForm) {

        registerForm.addEventListener('submit', async (e) => {

            e.preventDefault();

            const submit  = document.getElementById('register-submit');

            const alertEl = document.getElementById('register-alert');

            if (alertEl) { alertEl.style.display = 'none'; }

            const raw = Object.fromEntries(new FormData(registerForm));

            if (!raw.first_name || !raw.last_name) {

                if (alertEl) { alertEl.textContent = 'Please enter your first and last name.'; alertEl.className = 'alert alert-error'; alertEl.style.display = 'block'; }

                return;

            }

            if (!window.Security.isValidEmail(raw.email)) {

                if (alertEl) { alertEl.textContent = 'Please enter a valid email address.'; alertEl.className = 'alert alert-error'; alertEl.style.display = 'block'; }

                return;

            }

            if (raw.password.length < 12) {

                if (alertEl) { alertEl.textContent = 'Password must be at least 12 characters.'; alertEl.className = 'alert alert-error'; alertEl.style.display = 'block'; }

                return;

            }

            if (raw.password !== raw.confirm_password) {

                if (alertEl) { alertEl.textContent = 'Passwords do not match.'; alertEl.className = 'alert alert-error'; alertEl.style.display = 'block'; }

                return;

            }

            if (!raw.terms) {

                if (alertEl) { alertEl.textContent = 'You must agree to the terms of service.'; alertEl.className = 'alert alert-error'; alertEl.style.display = 'block'; }

                return;

            }

            submit.disabled = true;

            submit.textContent = 'Creating account...';

            try {

                await window.Auth.register({

                    first_name: raw.first_name.trim(),

                    last_name:  raw.last_name.trim(),

                    email:      raw.email.trim().toLowerCase(),

                    phone:      (raw.phone || '').trim() || null,

                    password:   raw.password,

                });

                registerForm.reset();

                if (window.toast) window.toast('Account created! Sign in with your new credentials.', 'success');

                // Carry over the redirect param so the user lands on the right page after login.

                const regParams = new URLSearchParams(window.location.search);

                const regRedirectTo = regParams.get('redirect');

                const loginDest = regRedirectTo ? 'login.html?redirect=' + encodeURIComponent(regRedirectTo) : 'login.html';

                setTimeout(() => { window.location.href = loginDest; }, 2500);

            } catch (err) {

                if (alertEl) { alertEl.textContent = err.message || 'Registration failed.'; alertEl.className = 'alert alert-error'; alertEl.style.display = 'block'; }

            } finally {

                submit.disabled = false;

                submit.textContent = 'Create account';

            }

        });

    }





    // Forgot Password Form

    const forgotForm = document.getElementById('forgot-form');

    if (forgotForm) {

        forgotForm.addEventListener('submit', async (e) => {

            e.preventDefault();

            const email = forgotForm.email.value.trim();

            if (!window.Security.isValidEmail(email)) {

                if (window.toast) window.toast('Please enter a valid email address', 'error');

                return;

            }

            try {

                const res = await window.api.forgotPassword(email);

                if (window.toast) window.toast('✅ Reset link sent! Check your email.', 'success');

                forgotForm.email.value = '';

            } catch (err) {

                if (window.toast) window.toast('❌ ' + (err.message || 'Failed to send reset email'), 'error');

            }

        });

    }



    // Reset Password Form

    const resetForm = document.getElementById('reset-form');

    if (resetForm) {

        resetForm.addEventListener('submit', async (e) => {

            e.preventDefault();

            const pwd     = resetForm.password.value;

            const confirm = resetForm.confirm_password.value;

            if (pwd !== confirm) {

                if (window.toast) window.toast('Passwords do not match', 'error');

                return;

            }

            try {

                const params = new URLSearchParams(window.location.search);

                const token  = params.get('token');

                await window.api.resetPassword(token, pwd);

                if (window.toast) window.toast('Password reset successful! You can now sign in.', 'success');

                setTimeout(() => { window.location.href = 'login.html'; }, 1500);

            } catch (err) {

                if (window.toast) window.toast(err.message || 'Reset failed', 'error');

            }

        });

    }



    // MFA Verification Form

    const mfaForm = document.getElementById('mfa-form');

    if (mfaForm) {

        mfaForm.addEventListener('submit', async (e) => {

            e.preventDefault();

            const code = mfaForm.code.value.trim();

            if (code.length !== 6) {

                if (window.toast) window.toast('Please enter the 6-digit code', 'error');

                return;

            }

            try {

                // During login (admin users), verify the emailed code against
                // the login-time endpoint to receive the final JWT tokens.
                if (window.Auth.mfaPending && window.Auth.completeMfaLogin) {
                    await window.Auth.completeMfaLogin(code);
                } else {
                    await window.api.mfaVerify(code);
                }

                await window.Auth.getProfile();

                if (window.initAuthState) window.initAuthState();

                if (window.toast) window.toast('Verified successfully!', 'success');

                const dest = (window.Auth.user && ['admin', 'super_admin'].includes(window.Auth.user.role))

                    ? 'admin-products.html'

                    : 'account.html';

                setTimeout(() => { window.location.href = dest; }, 500);

            } catch (err) {

                if (window.toast) window.toast(err.message || 'Verification failed', 'error');

            }

        });

    }

})();


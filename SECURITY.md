# Security Policy

## Reporting Vulnerabilities
If you discover a security vulnerability, please email **security@aurum-ghana.local** with details. We respond within 48 hours.

## Security Measures
- All passwords hashed with bcrypt (cost 12)
- JWT tokens with short TTL (15 min) + refresh tokens (7 days)
- HTTPS-only in production
- CSRF protection on state-changing requests
- Rate limiting on auth endpoints (5 attempts / 15 min)
- Input sanitization (escapeHtml, sanitizeUrl)
- CSP headers via meta tag injection
- HttpOnly + Secure + SameSite cookies
- Ghana phone validation (local format)
- Email validation on all forms
- Password strength requirements enforced
- Admin role checks on /admin* pages

## Data Protection
- No card details stored (Paystack handles all PCI-compliant processing)
- Personal data encrypted at rest
- Audit logs for all admin actions
- Account deletion available per user request

## Reporting a Bug
Please include:
1. Description of the issue
2. Steps to reproduce
3. Potential impact
4. Suggested fix (optional)
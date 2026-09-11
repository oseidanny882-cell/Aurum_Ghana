# Aurum Ghana Security Policy

## How We Protect Your Data

- **Payment security**: All payments are processed by Paystack (PCI-DSS compliant). We never see or store your card details.
- **Authentication**: Passwords are hashed with bcrypt (cost 12). JWT tokens expire after 15 minutes.
- **HTTPS**: Enforced in production. All data in transit is encrypted.
- **Cookies**: Auth tokens use HttpOnly, Secure, and SameSite flags.
- **Input validation**: All user input is sanitized against XSS and injection attacks.
- **Rate limiting**: Login attempts are limited to 5 per 15 minutes per IP.
- **Local data**: No sensitive personal data is stored in localStorage — only anonymous session tokens.

## Responsible Disclosure

If you discover a security vulnerability, email **security@aurum-ghana.local** with details. We respond within 48 hours.

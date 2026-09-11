"""
Aurum Ghana - Email service
"""
import smtplib, ssl, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app


def is_smtp_configured():
    """Return True when all required SMTP values are present."""
    cfg = current_app.config
    return all([
        cfg.get("SMTP_HOST"),
        cfg.get("SMTP_USER"),
        cfg.get("SMTP_PASS"),
    ])


def send_email(to: str, subject: str, body: str = "", html_body: str = "", from_addr: str = None):
    """
    Send an email via SMTP.
    Falls back silently on failure so email errors don't break the app.
    In dev mode (FLASK_ENV=development), if SMTP is not configured, the email
    body is printed to the server log so reset/verification links can still
    be used during local testing.
    """
    host = current_app.config.get("SMTP_HOST")
    port = current_app.config.get("SMTP_PORT", 587)
    user = current_app.config.get("SMTP_USER")
    password = current_app.config.get("SMTP_PASS")
    from_addr = from_addr or current_app.config.get("EMAIL_FROM")

    # If SMTP isn't configured, either log a warning (prod) or print the
    # body to the server log (dev) so devs can still test reset flows.
    if not all([host, user, password]):
        msg = (
            f"[email] SMTP not configured — would have sent to {to}: "
            f"subject={subject!r} body={body!r}"
        )
        current_app.logger.warning(msg)
        if os.getenv("FLASK_ENV", "production") == "development":
            print("=" * 70)
            print(msg)
            print("=" * 70)
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to

        if body:
            msg.attach(MIMEText(body, "plain", "utf-8"))
        if html_body:
            msg.attach(MIMEText(html_body, "html", "utf-8"))
        elif body:
            msg.attach(MIMEText(f"<pre>{body}</pre>", "html", "utf-8"))

        context = ssl.create_default_context()

        # Gmail intermittently throws "Connection unexpectedly closed" on
        # the first try (especially after several rapid sends or when the
        # network hiccups). A short retry loop makes login-OTP email delivery
        # far more reliable while still surfacing real (auth) failures.
        attempts = 0
        last_exc = None
        while attempts < 3:
            attempts += 1
            try:
                with smtplib.SMTP(host, port) as server:
                    server.starttls(context=context)
                    server.login(user, password)
                    server.sendmail(from_addr, [to], msg.as_string())
                current_app.logger.info(f"[email] Sent {subject!r} to {to}")
                return True
            except Exception as exc:
                last_exc = exc
                current_app.logger.warning(
                    f"[email] Attempt {attempts}/3 failed to {to}: {exc}")
                if attempts >= 3:
                    break
                import time
                time.sleep(1.5)

        raise last_exc

    except Exception as exc:
        current_app.logger.warning(f"[email] Send failed to {to}: {exc}")
        if os.getenv("FLASK_ENV", "production") == "development":
            print(f"[email] SEND FAILED to {to}: {exc}")
            print(f"[email] Body that would have been sent:\n{body}")
        return False

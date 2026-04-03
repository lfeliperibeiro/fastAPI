import os
import smtplib
from email.message import EmailMessage


def _smtp_settings():
    host = os.getenv("SMTP_HOST") or os.getenv("MAILTRAP_HOST") or "sandbox.smtp.mailtrap.io"
    port = int(os.getenv("SMTP_PORT") or os.getenv("MAILTRAP_PORT") or "2525")
    user = os.getenv("SMTP_USER") or os.getenv("MAILTRAP_USER")
    password = os.getenv("SMTP_PASSWORD") or os.getenv("MAILTRAP_PASSWORD")
    mail_from = os.getenv("MAIL_FROM", "noreply@localhost")
    return host, port, user, password, mail_from


def send_password_reset_email(to_email: str, reset_token: str, user_name: str | None = None) -> None:
    host, port, user, password, mail_from = _smtp_settings()
    if not user or not password:
        raise RuntimeError(
            "Configure credenciais SMTP do Mailtrap no .env na raiz do projeto "
            "(SMTP_USER e SMTP_PASSWORD, ou MAILTRAP_USER e MAILTRAP_PASSWORD). "
            "Em Mailtrap: Email Testing → Inbox → Integrations → SMTP."
        )

    base = os.getenv("PASSWORD_RESET_BASE_URL", "").rstrip("/")
    if base:
        reset_link = f"{base}?token={reset_token}"
    else:
        reset_link = reset_token

    greeting = f"Olá, {user_name}" if user_name else "Olá"
    body = f"""{greeting},

Recebemos um pedido para redefinir a senha da sua conta.

Use o link ou o token abaixo (válido por tempo limitado):
{reset_link}

Se você não pediu isso, ignore este e-mail.
"""

    msg = EmailMessage()
    msg["Subject"] = "Recuperação de senha"
    msg["From"] = mail_from
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)

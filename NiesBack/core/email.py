from email.message import EmailMessage
import smtplib, ssl
from typing import Iterable
from .settings import settings

def _build_message(to: str | Iterable[str], subject: str, body_text: str, body_html: str | None = None) -> EmailMessage:
    to_list = [to] if isinstance(to, str) else list(to)

    msg = EmailMessage()
    msg["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = subject

    # Corpo: texto simples sempre
    msg.set_content(body_text)

    # Alternativa HTML (se houver)
    if body_html:
        msg.add_alternative(body_html, subtype="html")

    return msg

def send_email(to: str | Iterable[str], subject: str, body_text: str, body_html: str | None = None) -> None:
    msg = _build_message(to, subject, body_text, body_html)

    if settings.MAIL_DISABLED:
        print("=== MAIL (DEV/disabled) ===")
        print("TO:", msg["To"])
        print("SUBJECT:", msg["Subject"])
        print("--- TEXT ---")
        print(body_text)
        if body_html:
            print("--- HTML ---")
            print(body_html)
        print("===========================")
        return

    context = ssl.create_default_context()

    if settings.MAIL_USE_SSL:
        with smtplib.SMTP_SSL(settings.MAIL_HOST, settings.MAIL_PORT, context=context, timeout=20) as server:
            if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.send_message(msg)
    else:
        with smtplib.SMTP(settings.MAIL_HOST, settings.MAIL_PORT, timeout=20) as server:
            server.ehlo()
            if settings.MAIL_USE_TLS:
                server.starttls(context=context)
                server.ehlo()
            if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.send_message(msg)

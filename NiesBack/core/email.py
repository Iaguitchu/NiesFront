from email.message import EmailMessage
import smtplib, ssl
from typing import Iterable
from .settings import settings

def _build_message(to: str | Iterable[str], subject: str, body_text: str, body_html: str | None = None) -> EmailMessage:
    if isinstance(to, str):
        to_list = [to]
    else:
        to_list = list(to)

    msg = EmailMessage()
    msg["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
    msg["To"] = ", ".join(to_list)
    msg["Subject"] = subject

    # corpo: texto simples (sempre) + html (opcional)
    msg.set_content(body_text)
    return msg

def send_email(to: str | Iterable[str], subject: str, body_text: str, body_html: str | None = None) -> None:
    """
    Envia email via SMTP. Se MAIL_DISABLED=true, apenas loga no console (DEV).
    Levanta exceções do smtplib se falhar.
    """
    msg = _build_message(to, subject, body_text, body_html)

    if settings.MAIL_DISABLED:
        # modo DEV: apenas loga
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

    # Conexão SMTP
    context = ssl.create_default_context()

    if settings.MAIL_USE_SSL:
        # SMTPS (porta comum: 465)
        with smtplib.SMTP_SSL(settings.MAIL_HOST, settings.MAIL_PORT, context=context, timeout=20) as server:
            if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.send_message(msg)
    else:
        # TLS explícito (STARTTLS) – porta comum: 587
        with smtplib.SMTP(settings.MAIL_HOST, settings.MAIL_PORT, timeout=20) as server:
            server.ehlo()
            if settings.MAIL_USE_TLS:
                server.starttls(context=context)
                server.ehlo()
            if settings.MAIL_USERNAME and settings.MAIL_PASSWORD:
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.send_message(msg)

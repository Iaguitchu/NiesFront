import smtplib
from email.message import EmailMessage
from core.settings import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM

def compose_verification_email(to_email: str, to_name: str, verify_url: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = "Confirme seu e-mail"
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email

    texto = f"""
Olá {to_name},

Clique para confirmar seu e-mail:
{verify_url}

Se você não solicitou, ignore esta mensagem.
"""
    html = f"""
<p>Olá {to_name},</p>
<p>Clique para confirmar seu e-mail:</p>
<p><a href="{verify_url}"><strong>Confirmar e-mail</strong></a></p>
<p>Se você não solicitou, ignore esta mensagem.</p>
"""

    msg.set_content(texto.strip())
    msg.add_alternative(html.strip(), subtype="html")
    return msg

def send_email(msg: EmailMessage) -> None:
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        if SMTP_USER:
            smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)

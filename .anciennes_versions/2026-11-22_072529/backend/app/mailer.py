"""Envoi d'e-mails par SMTP (bibliothèque standard, dans un fil pour ne pas bloquer l'API).

Sans SMTP_HOST (développement local), l'e-mail n'est pas envoyé : son contenu est écrit dans
le journal de l'API, pour pouvoir copier le code. En production, l'API refuse de démarrer
sans SMTP si la vérification des adresses est active (voir checks.py).
"""
import asyncio
import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

from app.config import get_settings

log = logging.getLogger("mangastudio.mail")


class MailError(Exception):
    pass


def _send_sync(to: str, subject: str, text: str, html: str) -> None:
    s = get_settings()
    msg = EmailMessage()
    msg["From"] = s.smtp_from or formataddr(("MangaStudio", s.smtp_user))
    msg["To"] = to
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid(domain=(s.smtp_user.split("@")[-1] or None))
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    ctx = ssl.create_default_context()
    if s.smtp_starttls:
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=20) as smtp:
            smtp.starttls(context=ctx)
            smtp.login(s.smtp_user, s.smtp_password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP_SSL(s.smtp_host, s.smtp_port, timeout=20, context=ctx) as smtp:
            smtp.login(s.smtp_user, s.smtp_password)
            smtp.send_message(msg)


async def send(to: str, subject: str, text: str, html: str) -> None:
    if not get_settings().smtp_host:
        log.warning("SMTP non configuré : e-mail pour %s non envoyé.\n%s", to, text)
        return
    try:
        await asyncio.to_thread(_send_sync, to, subject, text, html)
    except (OSError, smtplib.SMTPException) as e:
        log.exception("échec d'envoi à %s", to)
        raise MailError(str(e)) from e


async def send_code(to: str, name: str, code: str, minutes: int) -> None:
    text = (f"Bonjour {name},\n\nVoici votre code pour confirmer votre adresse sur MangaStudio :\n\n    {code}\n\n"
            f"Il est valable {minutes} minutes. Si vous n'avez pas créé de compte, ignorez cet e-mail.\n\nL'équipe MangaStudio")
    html = f"""<div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;color:#14110F">
<p>Bonjour {name},</p>
<p>Voici votre code pour confirmer votre adresse sur <b>MangaStudio</b> :</p>
<p style="font-size:32px;font-weight:bold;letter-spacing:8px;background:#FFFDF8;border:2px solid #14110F;padding:16px;text-align:center">{code}</p>
<p>Il est valable {minutes} minutes. Si vous n'avez pas créé de compte, ignorez cet e-mail.</p>
<p>L'équipe MangaStudio</p></div>"""
    await send(to, f"{code} est votre code MangaStudio", text, html)

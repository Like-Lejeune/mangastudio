"""Domaines d'adresses e-mail jetables (boîtes temporaires sans inscription), refusés à l'inscription.

Liste volontairement courte : les services les plus utilisés. Pour en ajouter sans toucher au code :
BLOCKED_EMAIL_DOMAINS=domaine1.com,domaine2.net dans le fichier .env.
"""
from app.config import get_settings

DOMAINS = {
    "yopmail.com", "yopmail.fr", "yopmail.net", "cool.fr.nf", "jetable.fr.nf", "courriel.fr.nf", "moncourrier.fr.nf",
    "mailinator.com", "mailinator.net", "guerrillamail.com", "guerrillamail.net", "guerrillamail.org", "sharklasers.com",
    "grr.la", "10minutemail.com", "10minutemail.net", "temp-mail.org", "tempmail.com", "tempmail.net", "tempmailo.com",
    "temp-mail.io", "throwawaymail.com", "trashmail.com", "trashmail.net", "getnada.com", "nada.email", "dispostable.com",
    "maildrop.cc", "mailnesia.com", "mintemail.com", "mohmal.com", "emailondeck.com", "fakeinbox.com", "spamgourmet.com",
    "mailcatch.com", "jetable.org", "mytemp.email", "tempr.email", "discard.email", "burnermail.io", "inboxkitten.com",
    "1secmail.com", "1secmail.net", "1secmail.org", "byom.de", "trash-mail.com", "minuteinbox.com", "emailfake.com",
    "crazymailing.com", "tmpmail.org", "tmpmail.net", "mail.tm", "mailsac.com", "anonbox.net", "spambox.us",
}


def is_disposable(email: str) -> bool:
    domain = email.rsplit("@", 1)[-1].strip().lower()
    extra = {d.strip().lower() for d in get_settings().blocked_email_domains.split(",") if d.strip()}
    return domain in DOMAINS or domain in extra or any(domain.endswith("." + d) for d in DOMAINS | extra)

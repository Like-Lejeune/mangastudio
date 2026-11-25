"""Messages de l'API en anglais.

Le code écrit ses messages en français, comme avant. Quand la requête demande l'anglais
(en-tête Accept-Language: en…, envoyé par le site selon le bouton FR / EN), les messages connus
sont traduits au moment de répondre : erreurs, statut des épisodes, paiements, concours.
Un message absent du catalogue reste en français : rien ne casse, il manque seulement la traduction.
"""
import re
from contextvars import ContextVar

_lang: ContextVar[str] = ContextVar("lang", default="fr")


def lang() -> str:
    return _lang.get()


def parse_accept_language(header: str | None) -> str:
    first = (header or "").split(",")[0].strip().lower()
    return "en" if first.startswith("en") else "fr"


class LanguageMiddleware:
    """Lit Accept-Language et fixe la langue de la requête (ASGI pur : compatible avec les réponses en flux)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        header = next((v.decode() for k, v in scope.get("headers", []) if k == b"accept-language"), None)
        token = _lang.set(parse_accept_language(header))
        try:
            await self.app(scope, receive, send)
        finally:
            _lang.reset(token)


PLAN_EN = {"Découverte": "Discovery", "Créateur": "Creator", "Studio": "Studio"}
STYLE_EN = {"Shōnen": "Shōnen", "Shōjo": "Shōjo", "Seinen": "Seinen", "Kodomo": "Kodomo", "Afro-manga": "Afro-manga"}

EXACT: dict[str, str] = {
    # Comptes et sessions
    "Connexion requise.": "Please sign in.",
    "Session expirée, reconnectez-vous.": "Your session has expired, please sign in again.",
    "Compte introuvable.": "Account not found.",
    "Votre mot de passe a changé : reconnectez-vous.": "Your password has changed: please sign in again.",
    "Ce compte est suspendu. Contactez le support.": "This account is suspended. Please contact support.",
    "Confirmez d'abord votre adresse e-mail avec le code reçu.": "Please confirm your email address first with the code we sent you.",
    "Réservé aux administrateurs.": "Administrators only.",
    "L'e-mail n'a pas pu partir. Réessayez dans un instant avec « Renvoyer le code ».": "The email could not be sent. Try again in a moment with “Resend the code”.",
    "L'e-mail n'a pas pu partir. Réessayez dans un instant.": "The email could not be sent. Please try again in a moment.",
    "Les adresses e-mail temporaires ne sont pas acceptées. Utilisez votre adresse habituelle.": "Temporary email addresses are not accepted. Please use your usual address.",
    "Un compte existe déjà avec cette adresse.": "An account already exists with this address.",
    "Ce code a expiré. Demandez-en un nouveau.": "This code has expired. Please request a new one.",
    "Ce code n'est plus valable. Demandez-en un nouveau.": "This code is no longer valid. Please request a new one.",
    "Trop d'essais. Demandez un nouveau code.": "Too many attempts. Please request a new code.",
    "Code incorrect. Demandez un nouveau code.": "Wrong code. Please request a new code.",
    "Adresse ou mot de passe incorrect.": "Wrong email or password.",
    # Budget
    "Le studio a atteint sa capacité de dessin pour aujourd'hui. Réessayez demain : aucun crédit n'a été utilisé.":
        "The studio has reached its drawing capacity for today. Please try again tomorrow: no credits were used.",
    # Séries, personnages, épisodes
    "Ce texte contient des mots non autorisés.": "This text contains words that are not allowed.",
    "Photo illisible : JPEG, PNG ou WebP attendu.": "Unreadable photo: JPEG, PNG or WebP expected.",
    "Photo illisible : le fichier est abîmé.": "Unreadable photo: the file is damaged.",
    "Série introuvable.": "Series not found.",
    "Confirmez que vous avez l'accord de la personne sur la photo.": "Please confirm you have the consent of the person in the photo.",
    "Personnage introuvable.": "Character not found.",
    "Ce personnage est déjà dessiné : pour garder la cohérence des épisodes, créez plutôt un nouveau personnage.":
        "This character has already been drawn: to keep episodes consistent, create a new character instead.",
    "Épisode introuvable.": "Episode not found.",
    "Un épisode de cette série est déjà en cours de génération.": "An episode of this series is already being generated.",
    "Un épisode de cette série est interrompu : reprenez-le ou abandonnez-le (page de l'épisode) avant d'en lancer un nouveau.":
        "An episode of this series was interrupted: resume or abandon it (on the episode page) before starting a new one.",
    "Un des personnages n'appartient pas à cette série.": "One of the characters does not belong to this series.",
    "Seul un épisode interrompu peut être repris.": "Only an interrupted episode can be resumed.",
    "Seul un épisode interrompu ou refusé peut être abandonné.": "Only an interrupted or refused episode can be abandoned.",
    "Abandonnez d'abord l'épisode : seul un épisode abandonné peut être supprimé.": "Abandon the episode first: only an abandoned episode can be deleted.",
    "Un épisode est en cours de création : attendez qu'il se termine avant de supprimer la série.":
        "An episode is being created: wait for it to finish before deleting the series.",
    "Page introuvable.": "Page not found.",
    "L'épisode est encore en cours de génération.": "The episode is still being generated.",
    "Le dessinateur IA a refusé une image de cet épisode (personnage ou scène trop proche d'une œuvre existante, ou contenu interdit). "
    "Modifiez la série ou les personnages, puis lancez un nouvel épisode.":
        "The AI artist refused an image in this episode (a character or scene too close to an existing work, or forbidden content). "
        "Edit the series or characters, then start a new episode.",
    # Partage, PDF
    "Seul un épisode terminé peut être partagé.": "Only a finished episode can be shared.",
    "Le chapitre n'est pas terminé.": "The chapter is not finished.",
    # Galerie
    "Seul un épisode terminé peut être publié.": "Only a finished episode can be published.",
    "Acceptez les règles de publication pour proposer votre chapitre.": "Please accept the publishing rules to submit your chapter.",
    "Cette histoire n'est pas (ou plus) publiée.": "This story is not (or no longer) published.",
    "Cette histoire n'est pas publiée.": "This story is not published.",
    "Vous ne pouvez pas aimer votre propre histoire.": "You can't like your own story.",
    "Histoire introuvable.": "Story not found.",
    "Retiré par l'auteur": "Withdrawn by the author",
    # Avis
    "Cochez l'accord de publication pour envoyer votre avis.": "Please tick the publishing consent box to send your review.",
    "Avis introuvable.": "Review not found.",
    # Paiements
    "Le paiement mobile money n'est pas encore configuré.": "Mobile money payment is not set up yet.",
    "Un don se fait par mobile money, avec un montant d'au moins 500 FCFA.": "Donations are made by mobile money, for at least 500 FCFA.",
    "Les petits packs se paient par mobile money.": "Small packs are paid by mobile money.",
    "Le paiement par carte n'est pas encore disponible.": "Card payment is not available yet.",
    "Indiquez le numéro de téléphone et l'opérateur.": "Please enter the phone number and the operator.",
    "Validez le paiement sur votre téléphone.": "Confirm the payment on your phone.",
    "Paiement introuvable.": "Payment not found.",
    "La demande de paiement n'a pas abouti. Réessayez.": "The payment request did not go through. Please try again.",
    "Paiement refusé ou annulé.": "Payment refused or cancelled.",
    # Concours
    "Concours introuvable.": "Contest not found.",
    "Les inscriptions ne sont pas ouvertes.": "Entries are not open yet.",
    "Les inscriptions sont closes.": "Entries are closed.",
    "Chapitre introuvable.": "Chapter not found.",
    "Proposez d'abord ce chapitre à la galerie depuis la page de l'épisode.": "First submit this chapter to the gallery from the episode page.",
    "Cette histoire est déjà inscrite.": "This story is already entered.",
    "Inscription introuvable.": "Entry not found.",
    "Le concours est clos : l'inscription ne peut plus être retirée.": "The contest is closed: the entry can no longer be withdrawn.",
    "Ce concours n'accepte que les chapitres créés depuis son ouverture.": "This contest only accepts chapters created since it opened.",
    "Les résultats sont proclamés : le concours ne se modifie plus.": "Results have been announced: the contest can no longer be edited.",
    "Les résultats sont proclamés.": "Results have been announced.",
    "Les résultats se proclament après la clôture, une seule fois.": "Results are announced once, after the contest closes.",
    # Administration et services (rarement vus par le public)
    "Publication introuvable.": "Publication not found.",
    "Indiquez un motif : il est montré à l'auteur.": "Give a reason: it is shown to the author.",
    "Seule une histoire publiée peut être un coup de cœur.": "Only a published story can be a staff pick.",
    "Notification refusée.": "Notification rejected.",
}

_s = r"s?"   # pluriel facultatif


def _plan(m: re.Match) -> str:
    return PLAN_EN.get(m.group("plan"), m.group("plan"))


PATTERNS: list[tuple[re.Pattern, object]] = [
    (re.compile(r"^Trop de tentatives\. Réessayez dans (?P<n>\d+) minutes?\.$"),
     lambda m: f"Too many attempts. Try again in {m['n']} minute{'s' if int(m['n']) > 1 else ''}."),
    (re.compile(r"^Code incorrect\. Encore (?P<n>\d+) essais?\.$"),
     lambda m: f"Wrong code. {m['n']} attempt{'s' if int(m['n']) > 1 else ''} left."),
    (re.compile(r"^Il faut (?P<a>\d+) crédits, il en reste (?P<b>-?\d+)\.$"),
     lambda m: f"You need {m['a']} credits; you have {m['b']} left."),
    (re.compile(r"^Le plan (?P<plan>.+?) permet de (?P<a>\d+) à (?P<b>\d+) pages par épisode\.$"),
     lambda m: f"The {_plan(m)} plan allows {m['a']} to {m['b']} pages per episode."),
    (re.compile(r"^Le plan (?P<plan>.+?) permet (?P<n>\d+) personnages par épisode\.$"),
     lambda m: f"The {_plan(m)} plan allows {m['n']} characters per episode."),
    (re.compile(r"^La couleur n'est pas incluse dans le plan (?P<plan>.+?)\.$"),
     lambda m: f"Colour is not included in the {_plan(m)} plan."),
    (re.compile(r"^Le redessin à la demande n'est pas inclus dans le plan (?P<plan>.+?)\.$"),
     lambda m: f"On-demand redraws are not included in the {_plan(m)} plan."),
    (re.compile(r"^Photo trop lourde : (?P<n>\d+) Mo au plus\.$"),
     lambda m: f"Photo too large: {m['n']} MB maximum."),
    (re.compile(r"^Vous avez téléchargé (?P<n>\d+) chapitres ce mois-ci\. Passez à un plan payant pour des PDF illimités et sans filigrane\.$"),
     lambda m: f"You have downloaded {m['n']} chapters this month. Upgrade to a paid plan for unlimited, watermark-free PDFs."),
    (re.compile(r"^« (?P<nom>.+?) » est un personnage protégé par le droit d'auteur : le dessinateur IA refusera de le dessiner\. "
                r"Inventez votre propre personnage \(un autre nom et une autre apparence\) : vous pourrez lui donner le même caractère\.$"),
     lambda m: f"“{m['nom']}” is a copyrighted character: the AI artist will refuse to draw it. "
               "Invent your own character (a different name and look): you can give it the same personality."),
    (re.compile(r"^Le dessinateur IA refuse de dessiner (?P<qui>.+?)\. C'est presque toujours parce que le nom ou l'apparence "
                r"ressemble à un personnage existant \(protégé par le droit d'auteur\), ou à un contenu interdit\. "
                r"Modifiez ce personnage depuis la page de la série \(autre nom, autre apparence\), puis lancez un nouvel épisode\. "
                r"Les crédits non utilisés vous ont été rendus\.$"),
     lambda m: "The AI artist refuses to draw " + m["qui"].replace("« ", "“").replace(" »", "”").replace(" et ", " and ")
               + ". This almost always means the name or look resembles an existing (copyrighted) character, or forbidden content. "
               "Edit this character from the series page (different name, different look), then start a new episode. "
               "Unused credits have been refunded."),
    (re.compile(r"^Pages à refaire : (?P<p>.+)\.$"), lambda m: f"Pages to redo: {m['p']}."),
    (re.compile(r"^La génération s'est interrompue \((?P<e>\w+)\)\. Vous pouvez la reprendre\.$"),
     lambda m: f"Generation was interrupted ({m['e']}). You can resume it."),
    (re.compile(r"^Le scénario contient une scène ou un mot non autorisé : (?P<p>.+)$"),
     lambda m: f"The script contains a forbidden scene or word: {m['p']}"),
    (re.compile(r"^Montant reçu \((?P<a>\d+)\) inférieur au prix \((?P<b>\d+)\)\.$"),
     lambda m: f"Amount received ({m['a']}) is lower than the price ({m['b']})."),
    (re.compile(r"^Ce concours impose le style (?P<s>.+?)\.$"),
     lambda m: f"This contest requires the {STYLE_EN.get(m['s'], m['s'])} style."),
    (re.compile(r"^Vous avez déjà inscrit (?P<n>\d+) histoires? : c'est le maximum pour ce concours\.$"),
     lambda m: f"You have already entered {m['n']} stor{'ies' if int(m['n']) > 1 else 'y'}: that's the maximum for this contest."),
]


def tr(text, to: str | None = None):
    """Traduit un message français connu si la langue demandée est l'anglais. Sinon, le renvoie tel quel."""
    if not isinstance(text, str) or not text or (to or lang()) != "en":
        return text
    if text in EXACT:
        return EXACT[text]
    for rx, repl in PATTERNS:
        m = rx.match(text)
        if m:
            return repl(m)  # type: ignore[operator]
    return text


def tr_detail(detail):
    """Le champ `detail` d'une erreur : texte, ou objet avec un `message`."""
    if isinstance(detail, str):
        return tr(detail)
    if isinstance(detail, dict) and isinstance(detail.get("message"), str):
        return {**detail, "message": tr(detail["message"])}
    return detail

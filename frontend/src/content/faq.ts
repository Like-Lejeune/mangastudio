import { pick } from "@/lib/i18n";

/** Questions fréquentes, par rubrique (français et anglais). Le texte accepte des retours à la ligne simples. */
export type Question = { q: string; r: string };

const FAQ_FR: { rubrique: string; questions: Question[] }[] = [
  {
    rubrique: "Découvrir MangaStudio",
    questions: [
      { q: "Qu'est-ce que MangaStudio ?", r: "Un studio de manga en ligne. Vous décrivez une histoire et vos personnages ; MangaStudio écrit le scénario puis dessine chaque page, avec les bulles, dans le style que vous choisissez : shōnen, shōjo, seinen, kodomo ou afro-manga." },
      { q: "Quel style choisir ?", r: "Shōnen pour l'action et l'aventure, shōjo pour les émotions et la romance, seinen pour des récits adultes et réalistes, kodomo pour les enfants, afro-manga pour des personnages et des décors africains. La page « Styles » montre un exemple de chacun." },
      { q: "Faut-il savoir dessiner ?", r: "Non. Il suffit de raconter votre idée en quelques lignes et de présenter vos personnages. Vous pouvez ensuite guider chaque épisode : ce qui doit s'y passer, l'ambiance, la fin." },
      { q: "Combien de temps faut-il pour un épisode ?", r: "Quelques minutes, selon le nombre de pages. Vous suivez l'avancement en direct : scénario, fiches des personnages, puis chaque page au fur et à mesure qu'elle est dessinée." },
      { q: "Dans quelle langue sont les bulles ?", r: "En français ou en anglais : la langue se choisit à la création de la série." },
      { q: "Les personnages restent-ils les mêmes d'une page à l'autre ?", r: "Oui. Chaque personnage reçoit une fiche modèle (visage, coiffure, tenue) qui sert de référence pour toutes les pages et tous les épisodes de la série." },
    ],
  },
  {
    rubrique: "Crédits et paiement",
    questions: [
      { q: "À quoi correspond un crédit ?", r: "Un crédit = une image livrée : une page, une fiche de personnage ou une couverture. Le nombre de crédits nécessaires s'affiche avant de lancer l'épisode." },
      { q: "Comment gagner des crédits gratuits ?", r: "Trois façons, détaillées sur la page « Gagner des crédits » : inviter des amis avec votre lien (ils reçoivent 5 crédits, vous 10 quand ils terminent leur premier épisode, puis 25 à leur premier achat), accomplir les missions (premier épisode, premier partage, avis publié), et la recharge de la semaine : avec le plan gratuit, votre solde remonte à 5 crédits à votre première visite de la semaine." },
      { q: "Que se passe-t-il si un épisode s'interrompt ?", r: "Les crédits sont réservés au lancement, puis seules les images réellement livrées sont débitées. Si un épisode s'arrête en route, les crédits des images non livrées vous sont rendus, et vous pouvez reprendre l'épisode." },
      { q: "Comment payer ?", r: "Par mobile money, MTN Mobile Money ou Orange Money. Vous choisissez l'opérateur, indiquez votre numéro et validez le paiement sur votre téléphone. Le plan s'active dès que le paiement est confirmé." },
      { q: "L'abonnement se renouvelle-t-il tout seul ?", r: "Non. Un plan payé est actif 30 jours, sans prélèvement automatique. Vous le renouvelez quand vous le souhaitez depuis la page Abonnements." },
      { q: "Mes crédits expirent-ils ?", r: "Les crédits du plan valent pour la période de 30 jours. Ceux d'un pack de crédits n'expirent pas." },
      { q: "J'ai payé mais mon plan n'est pas actif.", r: "Attendez quelques minutes : la confirmation de l'opérateur peut arriver avec du retard, et la page se met à jour d'elle-même. Si rien ne change, écrivez-nous avec la date, le montant et le numéro utilisé." },
    ],
  },
  {
    rubrique: "Personnages et photos",
    questions: [
      { q: "Puis-je donner une photo à un personnage ?", r: "Oui, en JPEG, PNG ou WebP, 3 Mo au plus. N'utilisez que votre propre photo ou celle d'une personne qui vous a donné son accord : c'est demandé à l'envoi." },
      { q: "Combien de personnages par épisode ?", r: "Cela dépend de votre plan : le détail est sur la page Tarifs. Le plan Studio en accepte jusqu'à 10." },
    ],
  },
  {
    rubrique: "Contenus et règles",
    questions: [
      { q: "Pourquoi ma demande a-t-elle été refusée ?", r: "MangaStudio refuse les contenus sexuels, tout ce qui implique des mineurs de façon inappropriée, la violence extrême montrée en détail, la haine envers un groupe, l'apologie du terrorisme, et les mises en scène humiliantes de personnes réelles. Un refus a lieu avant le dessin : aucun crédit n'est débité." },
      { q: "« Capacité de dessin atteinte pour aujourd'hui » : qu'est-ce que ça veut dire ?", r: "Pour maîtriser ses coûts, la plateforme fixe une limite de dessin par jour. Quand elle est atteinte, les nouveaux épisodes sont refusés jusqu'au lendemain, sans débiter de crédit. Les épisodes déjà lancés vont jusqu'au bout." },
    ],
  },
  {
    rubrique: "Mon compte",
    questions: [
      { q: "Je ne reçois pas le code de confirmation.", r: "Regardez dans les courriers indésirables (spam), puis utilisez « Renvoyer le code » après une minute. Vérifiez aussi l'adresse affichée : en cas d'erreur, « Mauvaise adresse ? Recommencer » permet de vous réinscrire. Les adresses temporaires (yopmail, mailinator…) ne sont pas acceptées." },
      { q: "Pourquoi confirmer mon adresse e-mail ?", r: "Pour que les crédits offerts aillent à de vraies personnes : sans confirmation, des robots pourraient créer des comptes à la chaîne et épuiser la capacité de dessin de la plateforme. Vos crédits offerts arrivent dès la confirmation." },
      { q: "J'ai oublié mon mot de passe.", r: "Sur la page de connexion, cliquez sur « Mot de passe oublié ? » et indiquez votre adresse : vous recevez un code par e-mail pour choisir un nouveau mot de passe. Vos autres appareils sont alors déconnectés." },
      { q: "Comment donner mon avis ?", r: "À la fin d'un épisode, ou à tout moment depuis « Donner mon avis » en bas de page. Il est publié sur la page d'accueil après une rapide relecture, avec le nom que vous choisissez, jamais votre adresse e-mail. Vous pouvez le modifier ou le retirer quand vous voulez." },
      { q: "Comment supprimer mon compte ?", r: "Écrivez-nous depuis l'adresse de votre compte ; vos séries, personnages et photos seront supprimés." },
    ],
  },
  {
    rubrique: "Nous soutenir",
    questions: [
      { q: "À quoi servent les dons ?", r: "À payer les serveurs et les modèles d'intelligence artificielle qui dessinent les mangas, pour garder des prix accessibles et une offre gratuite. Un don ne donne pas de crédits : c'est un soutien. Merci !" },
    ],
  },
];

const FAQ_EN: { rubrique: string; questions: Question[] }[] = [
  {
    rubrique: "Discover MangaStudio",
    questions: [
      { q: "What is MangaStudio?", r: "An online manga studio. You describe a story and your characters; MangaStudio writes the script, then draws every page, with speech balloons, in the style you choose: shōnen, shōjo, seinen, kodomo or afro-manga." },
      { q: "Which style should I choose?", r: "Shōnen for action and adventure, shōjo for emotions and romance, seinen for adult, realistic stories, kodomo for children, afro-manga for African characters and settings. The “Styles” page shows an example of each." },
      { q: "Do I need to know how to draw?", r: "No. Just tell your idea in a few lines and introduce your characters. You can then guide each episode: what should happen, the mood, the ending." },
      { q: "How long does an episode take?", r: "A few minutes, depending on the number of pages. You follow the progress live: script, character sheets, then each page as it is drawn." },
      { q: "What language are the balloons in?", r: "French or English: you choose the language when you create the series." },
      { q: "Do characters stay the same from page to page?", r: "Yes. Each character gets a model sheet (face, hair, outfit) used as the reference for every page and every episode of the series." },
    ],
  },
  {
    rubrique: "Credits and payment",
    questions: [
      { q: "What is a credit?", r: "One credit = one delivered image: a page, a character sheet or a cover. The number of credits needed is shown before you start the episode." },
      { q: "How can I earn free credits?", r: "Three ways, detailed on the “Earn credits” page: invite friends with your link (they get 5 credits, you get 10 when they finish their first episode, then 25 on their first purchase), complete missions (first episode, first share, published review), and the weekly top-up: on the free plan, your balance goes back up to 5 credits on your first visit of the week." },
      { q: "What happens if an episode is interrupted?", r: "Credits are reserved at launch, then only the images actually delivered are charged. If an episode stops along the way, credits for undelivered images are refunded, and you can resume the episode." },
      { q: "How do I pay?", r: "By mobile money, MTN Mobile Money or Orange Money. Choose the operator, enter your number and confirm the payment on your phone. Your plan is activated as soon as the payment is confirmed." },
      { q: "Does the subscription renew automatically?", r: "No. A paid plan is active for 30 days, with no automatic charge. You renew it whenever you want from the Plans page." },
      { q: "Do my credits expire?", r: "Plan credits are valid for the 30-day period. Credits from a credit pack never expire." },
      { q: "I paid but my plan isn't active.", r: "Wait a few minutes: the operator's confirmation can be delayed, and the page updates by itself. If nothing changes, write to us with the date, the amount and the number you used." },
    ],
  },
  {
    rubrique: "Characters and photos",
    questions: [
      { q: "Can I give a character a photo?", r: "Yes, in JPEG, PNG or WebP, 3 MB maximum. Only use your own photo or one of a person who has given you their consent: you are asked to confirm it when uploading." },
      { q: "How many characters per episode?", r: "It depends on your plan: details are on the Pricing page. The Studio plan allows up to 10." },
    ],
  },
  {
    rubrique: "Content and rules",
    questions: [
      { q: "Why was my request refused?", r: "MangaStudio refuses sexual content, anything involving minors inappropriately, extreme violence shown in detail, hatred towards a group, glorification of terrorism, and humiliating depictions of real people. A refusal happens before drawing: no credits are charged." },
      { q: "“Drawing capacity reached for today”: what does it mean?", r: "To control its costs, the platform sets a daily drawing limit. When it is reached, new episodes are refused until the next day, without charging credits. Episodes already started run to the end." },
    ],
  },
  {
    rubrique: "My account",
    questions: [
      { q: "I don't receive the confirmation code.", r: "Check your spam folder, then use “Resend the code” after a minute. Also check the address shown: if it's wrong, “Wrong address? Start over” lets you sign up again. Temporary addresses (yopmail, mailinator…) are not accepted." },
      { q: "Why confirm my email address?", r: "So that free credits go to real people: without confirmation, bots could create accounts one after another and use up the platform's drawing capacity. Your free credits arrive as soon as you confirm." },
      { q: "I forgot my password.", r: "On the sign-in page, click “Forgot your password?” and enter your address: you'll receive a code by email to choose a new password. Your other devices are then signed out." },
      { q: "How do I leave a review?", r: "At the end of an episode, or at any time from “Leave a review” at the bottom of the page. It is published on the home page after a quick check, with the name you choose, never your email address. You can edit or remove it whenever you like." },
      { q: "How do I delete my account?", r: "Write to us from your account's email address; your series, characters and photos will be deleted." },
    ],
  },
  {
    rubrique: "Support us",
    questions: [
      { q: "What are donations used for?", r: "To pay for the servers and the AI models that draw the mangas, to keep prices affordable and a free plan available. A donation doesn't give credits: it's support. Thank you!" },
    ],
  },
];

/** Les questions dans la langue courante. */
export const faq = () => pick({ fr: FAQ_FR, en: FAQ_EN });

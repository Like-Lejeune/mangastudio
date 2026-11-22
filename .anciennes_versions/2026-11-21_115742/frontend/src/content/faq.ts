/** Questions fréquentes, par rubrique. Le texte accepte des retours à la ligne simples. */
export type Question = { q: string; r: string };

export const FAQ: { rubrique: string; questions: Question[] }[] = [
  {
    rubrique: "Découvrir MangaStudio",
    questions: [
      { q: "Qu'est-ce que MangaStudio ?", r: "Un studio de manga en ligne. Vous décrivez une histoire et vos personnages ; MangaStudio écrit le scénario puis dessine chaque page, avec les bulles, dans le style que vous choisissez (shōnen, shōjo, seinen, kodomo)." },
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
      { q: "J'ai oublié mon mot de passe.", r: "Écrivez-nous depuis l'adresse de votre compte : nous vous aidons à en définir un nouveau." },
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

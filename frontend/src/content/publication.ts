import { pick } from "@/lib/i18n";

/**
 * Règles de publication dans la galerie « À lire ».
 *
 * BROUILLON rédigé par l'équipe technique : à faire relire et valider par la personne
 * qui porte le volet juridique (conditions d'utilisation) avant d'ouvrir la galerie au public.
 * Une fois validé, passez VALIDE à true : la mention « version provisoire » disparaît.
 */
export const VALIDE = false;
export const MISE_A_JOUR = "24 novembre 2026";
export const MISE_A_JOUR_EN = "24 November 2026";

const REGLES_FR: { titre: string; points: string[] }[] = [
  {
    titre: "Ce que vous publiez",
    points: [
      "Vous publiez une histoire que vous avez créée vous-même sur MangaStudio : l'idée, les personnages et le texte sont les vôtres.",
      "Pas de personnages, de marques ou d'univers appartenant à d'autres (héros de mangas ou de films connus, logos…), sauf autorisation écrite.",
      "Pas de personnes réelles reconnaissables présentées de façon humiliante, mensongère ou sans leur accord.",
    ],
  },
  {
    titre: "Ce qui est refusé",
    points: [
      "Tout contenu sexuel impliquant des mineurs, sans exception, et tout contenu sexuel explicite.",
      "Les appels à la haine ou à la violence contre des personnes ou des groupes (origine, religion, sexe, handicap…).",
      "La violence gratuite présentée de façon complaisante, l'apologie du terrorisme ou de crimes.",
      "Les informations personnelles d'autrui (numéros, adresses…) et les arnaques.",
    ],
  },
  {
    titre: "Validation par l'équipe",
    points: [
      "Chaque chapitre est relu avant d'apparaître dans la galerie. La relecture peut prendre quelques jours.",
      "L'équipe peut refuser ou retirer un chapitre ; le motif vous est indiqué sur la page de l'épisode.",
      "Après correction, vous pouvez proposer à nouveau votre chapitre.",
    ],
  },
  {
    titre: "Vos droits",
    points: [
      "Vous restez propriétaire de votre histoire.",
      "En la publiant, vous autorisez MangaStudio à l'afficher gratuitement dans la galerie et sur la page d'accueil, et à en montrer des extraits pour faire connaître la plateforme, toujours avec votre nom d'auteur.",
      "Vous pouvez retirer votre chapitre de la galerie à tout moment, depuis la page de l'épisode. Il disparaît alors de la galerie et de l'accueil.",
      "Votre nom d'auteur est affiché ; votre adresse e-mail ne l'est jamais.",
    ],
  },
  {
    titre: "Les « j'aime »",
    points: [
      "Un seul « j'aime » par compte confirmé et par histoire. On ne peut pas aimer sa propre histoire.",
      "Acheter, échanger ou fabriquer des « j'aime » (faux comptes, comptes multiples) est interdit : les « j'aime » concernés sont annulés et l'histoire peut être retirée.",
      "« Les plus aimées de la semaine » comptent les « j'aime » des 7 derniers jours. Les « Coups de cœur » sont choisis par l'équipe.",
    ],
  },
];

const REGLES_EN: { titre: string; points: string[] }[] = [
  {
    titre: "What you publish",
    points: [
      "You publish a story you created yourself on MangaStudio: the idea, the characters and the text are yours.",
      "No characters, brands or universes that belong to others (well-known manga or film heroes, logos…), unless you have written permission.",
      "No recognisable real people shown in a humiliating or misleading way, or without their consent.",
    ],
  },
  {
    titre: "What is refused",
    points: [
      "Any sexual content involving minors, without exception, and any explicit sexual content.",
      "Calls for hatred or violence against people or groups (origin, religion, sex, disability…).",
      "Gratuitous violence shown approvingly, glorification of terrorism or crime.",
      "Other people's personal information (numbers, addresses…) and scams.",
    ],
  },
  {
    titre: "Review by the team",
    points: [
      "Every chapter is reviewed before it appears in the gallery. The review can take a few days.",
      "The team can refuse or remove a chapter; the reason is shown to you on the episode page.",
      "Once corrected, you can submit your chapter again.",
    ],
  },
  {
    titre: "Your rights",
    points: [
      "You remain the owner of your story.",
      "By publishing it, you allow MangaStudio to show it for free in the gallery and on the home page, and to show excerpts to promote the platform, always with your author name.",
      "You can remove your chapter from the gallery at any time, from the episode page. It then disappears from the gallery and the home page.",
      "Your author name is shown; your email address never is.",
    ],
  },
  {
    titre: "Likes",
    points: [
      "One like per confirmed account and per story. You can't like your own story.",
      "Buying, trading or faking likes (fake accounts, multiple accounts) is forbidden: those likes are cancelled and the story may be removed.",
      "“Most liked this week” counts likes from the last 7 days. “Staff picks” are chosen by the team.",
    ],
  },
];

/** Les règles dans la langue courante. */
export const regles = () => pick({ fr: REGLES_FR, en: REGLES_EN });
export const miseAJour = () => pick({ fr: MISE_A_JOUR, en: MISE_A_JOUR_EN });

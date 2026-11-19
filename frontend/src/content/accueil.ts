/**
 * Contenu éditable de la page d'accueil.
 *
 * Ne mettez ici que de vrais partenaires et de vrais avis, avec l'accord écrit des personnes
 * et des entreprises citées. Une section reste masquée tant que sa liste est vide.
 *
 * Logos : déposez les fichiers dans frontend/public/partenaires/ (SVG de préférence, ou PNG
 * sur fond transparent, environ 200 × 80 px), puis indiquez « /partenaires/nom.svg ».
 * Sans logo, le nom de l'entreprise s'affiche en toutes lettres.
 * Photos des avis : frontend/public/avis/ ; sans photo, les initiales s'affichent.
 */

export type Partenaire = { nom: string; logo?: string; lien?: string };

export type Avis = {
  texte: string;        // 280 caractères au plus pour rester lisible dans la bulle
  nom: string;          // tel que la personne accepte d'être citée
  role: string;         // ex. « Autrice de la série … », « Enseignante, Douala »
  photo?: string;
  note?: 1 | 2 | 3 | 4 | 5;
};

export const PARTENAIRES: Partenaire[] = [
  // { nom: "Nom de l'entreprise", logo: "/partenaires/entreprise.svg", lien: "https://…" },
];

export const AVIS: Avis[] = [
  // { texte: "…", nom: "Prénom N.", role: "…", note: 5 },
];

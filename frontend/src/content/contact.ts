/**
 * Coordonnées affichées sur la plateforme (pied de page, page Contact, page Nous soutenir).
 * Un champ laissé vide n'est pas affiché. Numéros au format international : +237 6XX XX XX XX.
 */
export const CONTACT = {
  email: "contact@psikalab.space",                 // ex. contact@psikalab.space
  orange: "6 95 24 95 49",                // numéro Orange (appels, WhatsApp si `whatsapp` vaut true)
  mtn: "6 75 65 99 36",                   // numéro MTN
  whatsapp: true,           // true : ajoute un lien WhatsApp sur les numéros
  horaires: "Du lundi au samedi, 8 h – 18 h (heure de Douala)",
};

/**
 * Dons envoyés directement, sans compte MangaStudio (dépôt Orange Money ou MTN MoMo).
 * `titulaire` : le nom qui s'affiche chez le donateur au moment de valider le dépôt,
 * pour qu'il sache que c'est le bon destinataire.
 */
export const DONS_DIRECTS = {
  orangeMoney: { numero: "6 95 24 95 49", titulaire: "" },
  mtnMomo: { numero: "6 75 65 9936", titulaire: "" },
};

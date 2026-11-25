/**
 * Coordonnées affichées sur la plateforme (pied de page, page Contact, page Nous soutenir).
 * Un champ laissé vide n'est pas affiché. Numéros au format international : +237 6XX XX XX XX.
 */
export const CONTACT = {
  email: "",                 // ex. contact@psikalab.space
  orange: "",                // numéro Orange (appels, WhatsApp si `whatsapp` vaut true)
  mtn: "",                   // numéro MTN
  whatsapp: false,           // true : ajoute un lien WhatsApp sur les numéros
  horaires: "Du lundi au samedi, 8 h – 18 h (heure de Douala)",
  horairesEn: "Monday to Saturday, 8 am – 6 pm (Douala time)",
};

/**
 * Dons envoyés directement, sans compte MangaStudio (dépôt Orange Money ou MTN MoMo).
 * `titulaire` : le nom qui s'affiche chez le donateur au moment de valider le dépôt,
 * pour qu'il sache que c'est le bon destinataire.
 */
export const DONS_DIRECTS = {
  orangeMoney: { numero: "", titulaire: "" },
  mtnMomo: { numero: "", titulaire: "" },
};

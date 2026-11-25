/**
 * Règlement type des concours et concours prérempli.
 *
 * BROUILLON rédigé par l'équipe technique : la personne qui porte le volet juridique doit le relire et le valider
 * (tâche « Règlement du concours » du planning). L'administration le colle dans chaque concours et l'adapte :
 * le texte enregistré dans le concours est celui que voient les participants.
 */
export const REGLEMENT_TYPE = `1. Organisateur
Le concours est organisé par MangaStudio (PsikaLab). La participation est gratuite : aucun achat n'est nécessaire.

2. Qui peut participer
Toute personne qui a un compte MangaStudio confirmé. Les membres de l'équipe et du jury ne peuvent pas concourir.

3. Comment participer
Créez un chapitre sur MangaStudio pendant la période du concours, proposez-le à la galerie « À lire », puis inscrivez-le depuis la page du concours. Le chapitre doit respecter le thème, le style demandé s'il y en a un, et les règles de publication de la galerie.

4. Ce qui est refusé
Les chapitres qui reprennent des personnages, des univers ou des marques appartenant à d'autres, ceux qui ne respectent pas les règles de publication, et toute tentative de fausser les « j'aime » (faux comptes, comptes multiples, achat ou échange de « j'aime »). L'organisateur peut disqualifier un chapitre en donnant le motif.

5. Classement
Note du jury sur 20 (60 %) : respect du thème, originalité de l'histoire, qualité de la narration.
« J'aime » reçus pendant le concours (40 %) : l'histoire la plus aimée obtient 20, les autres en proportion.
En cas d'égalité, l'histoire qui a le plus de « j'aime » passe devant, puis celle inscrite la première.

6. Lots
Les lots sont indiqués sur la page du concours. Ils sont crédités automatiquement sur le compte des gagnants à la proclamation des résultats. Ils ne sont ni échangeables ni convertibles en argent.

7. Résultats
Les résultats sont publiés sur la page du concours après la délibération du jury. Les chapitres gagnants restent dans la galerie avec la mention de leur prix.

8. Droits
Chaque auteur reste propriétaire de son histoire. En participant, il autorise MangaStudio à la montrer sur la plateforme et à en montrer des extraits pour annoncer le concours et ses résultats, toujours avec son nom d'auteur.

9. Données
Seuls le nom d'auteur et l'histoire sont montrés publiquement. L'adresse e-mail n'est jamais affichée.

10. Contact
Pour toute question : page « Nous contacter ».`;

/** Premier concours prévu au planning : du 21 décembre au 17 janvier, en afro-manga. */
export const CONTES_AFRIQUE = {
  title: "Contes et légendes d'Afrique",
  theme: "Revisitez un conte, une légende ou un mythe d'Afrique en afro-manga.",
  description:
    "Mami Wata, Soundiata, la tortue et ses ruses, les esprits de la forêt… Choisissez un conte que vous connaissez, ou inventez une légende de votre village, et racontez-le à votre façon en un chapitre d'afro-manga. Le jury regarde le respect du thème, l'originalité et la façon de raconter ; les lecteurs votent avec leurs « j'aime ».",
  style: "afro",
  starts: "2026-12-21T00:00",
  ends: "2027-01-17T23:59",
  prizes: [
    { rank: 1, credits: 200, studio_days: 30 },
    { rank: 2, credits: 100, studio_days: 0 },
    { rank: 3, credits: 50, studio_days: 0 },
  ],
};

/**
 * Les styles de dessin proposés à la création d'une série.
 * L'identifiant (id) doit correspondre à celui de l'API (backend/app/pipeline/prompts.py).
 * Image d'exemple : frontend/public/styles/<id>.webp, produite par  python -m scripts.exemples_styles
 */
export type StyleManga = {
  id: "shonen" | "shojo" | "seinen" | "kodomo" | "afro";
  nom: string;
  origine: string;       // d'où vient le mot
  accroche: string;      // une ligne, affichée dans le formulaire
  description: string;
  ideal: string[];       // pour quelles histoires
  reperes?: string;      // séries connues dans ce style
  nouveau?: boolean;
};

export const STYLES_MANGA: StyleManga[] = [
  {
    id: "shonen",
    nom: "Shōnen",
    origine: "« jeune garçon » en japonais",
    accroche: "Action, combats et dépassement de soi",
    description: "Le style des grandes aventures : traits énergiques, lignes de vitesse, cadrages spectaculaires et héros qui ne lâchent jamais rien. Les émotions sont fortes et les scènes d'action occupent toute la page.",
    ideal: ["Aventure", "Combats", "Rivalité", "Sport", "Fantastique"],
    reperes: "Naruto, One Piece, Dragon Ball",
  },
  {
    id: "shojo",
    nom: "Shōjo",
    origine: "« jeune fille » en japonais",
    accroche: "Émotions, relations et romance",
    description: "Un trait fin et délicat, de grands yeux expressifs, des fonds décorés de fleurs ou de lumière. Le shōjo met les sentiments au premier plan : amitiés, amours, doutes et moments de vie.",
    ideal: ["Romance", "Amitié", "Vie au lycée", "Magie", "Drame"],
    reperes: "Sailor Moon, Fruits Basket, Card Captor Sakura",
  },
  {
    id: "seinen",
    nom: "Seinen",
    origine: "« jeune homme » en japonais, pour un public adulte",
    accroche: "Récits adultes, sombres ou réalistes",
    description: "Des proportions réalistes, des ombres profondes et beaucoup de détails. Le seinen raconte des histoires plus complexes et plus graves : enquêtes, guerres, questions morales, vie d'adulte.",
    ideal: ["Polar", "Thriller", "Histoire", "Science-fiction", "Drame social"],
    reperes: "Monster, Vagabond, Vinland Saga",
  },
  {
    id: "kodomo",
    nom: "Kodomo",
    origine: "« enfant » en japonais",
    accroche: "Pour les enfants : simple, doux et drôle",
    description: "Des formes rondes, des contours épais et des visages souriants. Le kodomo s'adresse aux plus jeunes : histoires courtes, humour, animaux qui parlent et petites leçons de vie.",
    ideal: ["Contes", "Humour", "Animaux", "Apprentissage", "Histoires du soir"],
    reperes: "Doraemon, Pokémon, Hamtaro",
  },
  {
    id: "afro",
    nom: "Afro-manga",
    origine: "le manga raconté depuis l'Afrique",
    accroche: "Personnages et décors africains, énergie du manga",
    description: "Le découpage et l'encrage du manga, au service de personnages et de lieux africains : marchés, moto-taxis, quartiers, villages, savane et forêt. Les teintes de peau, les coiffures (tresses, locks, foulards) et les tissus (wax, kente, bogolan, ndop) sont dessinés avec soin, et les motifs deviennent des trames graphiques.",
    ideal: ["Histoires d'ici", "Légendes et contes", "Vie de quartier", "Afrofuturisme", "Aventure"],
    nouveau: true,
  },
];

export const styleParId = (id: string) => STYLES_MANGA.find((s) => s.id === id);

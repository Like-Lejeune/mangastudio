import { pick } from "@/lib/i18n";

/**
 * Les styles de dessin proposés à la création d'une série (français et anglais).
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

const STYLES_FR: StyleManga[] = [
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

const STYLES_EN: StyleManga[] = [
  {
    id: "shonen", nom: "Shōnen", origine: "“young boy” in Japanese",
    accroche: "Action, fights and pushing your limits",
    description: "The style of great adventures: energetic lines, speed lines, spectacular framing and heroes who never give up. Emotions run high and action scenes fill the whole page.",
    ideal: ["Adventure", "Fights", "Rivalry", "Sports", "Fantasy"],
    reperes: "Naruto, One Piece, Dragon Ball",
  },
  {
    id: "shojo", nom: "Shōjo", origine: "“young girl” in Japanese",
    accroche: "Emotions, relationships and romance",
    description: "Fine, delicate lines, big expressive eyes, backgrounds decorated with flowers or light. Shōjo puts feelings first: friendships, love, doubts and slices of life.",
    ideal: ["Romance", "Friendship", "High-school life", "Magic", "Drama"],
    reperes: "Sailor Moon, Fruits Basket, Card Captor Sakura",
  },
  {
    id: "seinen", nom: "Seinen", origine: "“young man” in Japanese, for an adult audience",
    accroche: "Adult, dark or realistic stories",
    description: "Realistic proportions, deep shadows and lots of detail. Seinen tells more complex and serious stories: investigations, wars, moral questions, adult life.",
    ideal: ["Crime", "Thriller", "History", "Science fiction", "Social drama"],
    reperes: "Monster, Vagabond, Vinland Saga",
  },
  {
    id: "kodomo", nom: "Kodomo", origine: "“child” in Japanese",
    accroche: "For children: simple, gentle and funny",
    description: "Round shapes, thick outlines and smiling faces. Kodomo is for the youngest readers: short stories, humour, talking animals and little life lessons.",
    ideal: ["Tales", "Humour", "Animals", "Learning", "Bedtime stories"],
    reperes: "Doraemon, Pokémon, Hamtaro",
  },
  {
    id: "afro", nom: "Afro-manga", origine: "manga told from Africa",
    accroche: "African characters and settings, manga energy",
    description: "Manga panelling and inking in the service of African characters and places: markets, moto-taxis, neighbourhoods, villages, savannah and forest. Skin tones, hairstyles (braids, locs, headwraps) and fabrics (wax, kente, bogolan, ndop) are drawn with care, and patterns become graphic screentones.",
    ideal: ["Local stories", "Legends and tales", "Neighbourhood life", "Afrofuturism", "Adventure"],
    nouveau: true,
  },
];

/** Les styles dans la langue courante. */
export const stylesManga = () => pick({ fr: STYLES_FR, en: STYLES_EN });
/** Compatibilité : la liste (dans la langue courante au moment de l'appel). */
export const STYLES_MANGA = STYLES_FR;
export const styleParId = (id: string) => stylesManga().find((s) => s.id === id);

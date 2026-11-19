"""Liste de départ de la modération, chargée une fois par la migration 0003.

Après le chargement, tout se gère dans l'administration (Modération) : ajouter, retirer, passer
un mot de « bloquer » à « signaler ». Les termes sont écrits sans accents ni majuscules : la
comparaison ignore déjà accents, majuscules, chiffres à la place des lettres et lettres espacées.

« block » : le texte est refusé, rien n'est débité.
« flag »  : le texte passe, mais l'événement est noté au journal de modération. Pour les mots qui
            ont un usage légitime dans une histoire (un récit peut évoquer la drogue ou un attentat).
"""

TERMS: list[tuple[str, str]] = [
    # Contenu sexuel et nudité (règles socle : aucun contenu sexuel, jamais de mineur sexualisé)
    *[(t, "block") for t in (
        "porno", "pornographie", "pornographique", "porn", "hentai", "ecchi", "nsfw", "xxx",
        "sexe explicite", "acte sexuel", "rapport sexuel", "scene de sexe", "sex scene", "explicit sex",
        "tout nu", "toute nue", "entierement nu", "entierement nue", "completement nu", "completement nue",
        "nu integral", "nue integrale", "seins nus", "fully naked",
        "loli", "lolicon", "shota", "shotacon", "pedophile", "pedophilie", "pedopornographie",
        "viol", "violer", "violee", "rape", "raped", "inceste", "incest",
        "zoophilie", "bestialite", "bestiality", "necrophilie", "necrophilia",
    )],
    # Violence extrême
    *[(t, "block") for t in ("gore", "decapitation", "demembrement", "demembre", "eviscere", "dismember", "beheading")],
    # Mots à surveiller sans refuser
    *[(t, "flag") for t in (
        "nu", "nue", "nude", "naked", "suicide", "se suicider", "automutilation", "se scarifier",
        "torture", "terroriste", "attentat", "djihad", "nazi", "drogue", "cocaine",
    )],
]

SCENE_RULES: list[tuple[str, str]] = [
    ("violence-extreme", "Mutilation, démembrement, torture ou blessure sanglante montrés en gros plan et en détail. Les combats et un peu de sang restent permis."),
    ("suicide-automutilation", "Suicide ou automutilation montrés, encouragés, ou expliqués (méthode, gestes)."),
    ("haine", "Insulte, déshumanisation ou appel à la violence contre un groupe pour son origine, son ethnie, sa religion, son sexe, son orientation ou un handicap."),
    ("terrorisme-armes", "Apologie du terrorisme ou d'un groupe extrémiste, ou mode d'emploi pour fabriquer une arme ou un explosif."),
    ("drogues", "Consommation de drogue présentée comme désirable, ou explication pour en fabriquer ou en obtenir."),
    ("personnes-reelles", "Personne réelle identifiable (célébrité, responsable politique) mise en scène de façon humiliante, sexuelle ou diffamatoire."),
]

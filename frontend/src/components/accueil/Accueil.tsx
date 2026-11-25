import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { Check, Star } from "lucide-react";
import { api, type Plans } from "@/lib/api";
import { AVIS, PARTENAIRES, type Avis, type Partenaire } from "@/content/accueil";
import { btnClass, Onomatopee } from "@/components/ink";
import { cn } from "@/lib/utils";
import { STYLES_MANGA } from "@/content/styles";
import { VignetteStyle } from "@/components/StyleManga";
import { Esquisses, IconeEtape, PlancheAnimee } from "./Planche";
import { CarteHistoire } from "@/components/galerie/CarteHistoire";
import type { PageGalerie, TriGalerie } from "@/lib/galerie";

/** Ajoute .anime quand l'élément arrive à l'écran (une seule fois). */
function useRevele<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [vu, setVu] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || vu) return;
    if (!("IntersectionObserver" in window)) { setVu(true); return; }
    const io = new IntersectionObserver(([e]) => { if (e?.isIntersecting) { setVu(true); io.disconnect(); } }, { threshold: 0.2 });
    io.observe(el);
    return () => io.disconnect();
  }, [vu]);
  return [ref, vu] as const;
}

function Revele({ children, className, delai = 0, as: Tag = "div" }: { children: ReactNode; className?: string; delai?: number; as?: "div" | "li" }) {
  const [ref, vu] = useRevele<HTMLDivElement & HTMLLIElement>();
  return <Tag ref={ref} className={cn("revele", vu && "anime", className)} style={{ "--d": `${delai}s` } as CSSProperties}>{children}</Tag>;
}

function Titre({ sur, children, sous }: { sur: string; children: ReactNode; sous?: ReactNode }) {
  return (
    <Revele className="mx-auto mb-10 max-w-2xl text-center">
      <p className="label-caps mb-3">{sur}</p>
      <h2 className="font-display text-[32px] leading-[38px] sm:text-[44px] sm:leading-[50px]">{children}</h2>
      {sous && <p className="mt-4 text-[18px] leading-7 text-encre-douce">{sous}</p>}
    </Revele>
  );
}

const fcfa = (n: number) => `${new Intl.NumberFormat("fr-FR").format(n)} FCFA`;

export function Accueil() {
  const { data: plans } = useQuery({ queryKey: ["plans"], queryFn: () => api<Plans>("/plans"), staleTime: 3_600_000 });
  const studio = plans?.plans.find((p) => p.id === "studio");
  // Avis validés dans l'administration, puis ceux écrits à la main dans content/accueil.ts.
  const { data: avisEnLigne } = useQuery({ queryKey: ["avis-publics"], queryFn: () => api<(Avis & { id: string })[]>("/testimonials"), staleTime: 300_000 });
  const avis: Avis[] = [...(avisEnLigne ?? []), ...AVIS];
  // Galerie : rien n'est affiché tant qu'aucune histoire réelle n'est publiée.
  const galerie = (tri: TriGalerie) => ({ queryKey: ["galerie", "accueil", tri], queryFn: () => api<PageGalerie>(`/gallery?tri=${tri}&size=4`), staleTime: 300_000 });
  const semaine = (useQuery(galerie("semaine")).data?.items ?? []).filter((c) => (c.likes_week ?? 0) > 0);
  const coups = useQuery(galerie("coups")).data?.items ?? [];
  const recentes = useQuery(galerie("recentes")).data?.items ?? [];

  return (
    <div className="overflow-x-clip">
      {/* ───── En-tête : la planche se dessine ───── */}
      <section className="anime relative">
        <Esquisses className="pointer-events-none absolute inset-0 h-full w-full" />
        <div className="relative mx-auto grid max-w-[1200px] items-center gap-12 px-4 pb-16 pt-10 sm:px-6 lg:grid-cols-[1.15fr_1fr] lg:pb-24 lg:pt-16">
          <div>
            <p className="label-caps mb-4">Studio de manga en ligne</p>
            <h1 className="font-display text-[40px] leading-[46px] sm:text-[60px] sm:leading-[66px]">
              Votre idée. Vos personnages.{" "}
              <span className="relative inline-block whitespace-nowrap text-vermillon">
                Votre manga.
                <svg viewBox="0 0 300 20" preserveAspectRatio="none" className="absolute -bottom-2 left-0 h-3 w-full" aria-hidden>
                  <path pathLength={1} className="trait" style={{ "--d": "1.2s", "--t": "0.7s" } as CSSProperties}
                    d="M4,14 C80,4 180,4 296,10" fill="none" stroke="var(--encre)" strokeWidth="5" strokeLinecap="round" />
                </svg>
              </span>
            </h1>
            <p className="mt-8 max-w-xl text-[18px] leading-7 text-encre-douce">
              Décrivez une histoire en quelques lignes, présentez vos personnages : MangaStudio écrit le scénario et dessine chaque page, case après case, avec des bulles en français.
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Link to="/inscription" className={btnClass("primary")}>Créer mon premier épisode</Link>
              <a href="#tarifs" className={btnClass()}>Voir les tarifs</a>
            </div>
            <p className="mt-6 text-[14px] text-encre-douce">Gratuit pour commencer, sans carte : {plans ? `${plans.plans[0]?.credits} crédits offerts` : "des crédits offerts"} à l'inscription.</p>
          </div>
          <div className="relative mx-auto w-full max-w-[400px]">
            <div className="rotate-[1.5deg] border-2 border-encre bg-blanc shadow-ink-lg">
              <PlancheAnimee className="block h-auto w-full" />
            </div>
            <span className="pop absolute -left-6 -top-5" style={{ "--d": "4.6s" } as CSSProperties}>
              <Onomatopee>NEW !</Onomatopee>
            </span>
          </div>
        </div>
      </section>

      {/* ───── Partenaires ───── */}
      {PARTENAIRES.length > 0 && <BandeauPartenaires items={PARTENAIRES} />}

      {/* ───── Comment ça marche ───── */}
      <section className="mx-auto max-w-[1200px] px-4 py-20 sm:px-6">
        <Titre sur="Comment ça marche" sous="Trois étapes, quelques minutes, et votre épisode se lit page après page.">De l'idée à la planche</Titre>
        <ol className="grid gap-6 md:grid-cols-3">
          {([
            [1, "Racontez l'idée", "Une phrase ou une page : le pitch de votre série, son style (shōnen, shōjo, seinen, kodomo ou afro-manga) et sa langue."],
            [2, "Présentez vos personnages", `Nom, rôle, description et, si vous le voulez, une photo. Jusqu'à ${studio?.max_characters ?? 10} personnages par épisode, chacun avec sa fiche modèle.`],
            [3, "Regardez l'épisode se dessiner", `Le scénario est écrit puis vérifié, et chaque page est dessinée sous vos yeux. Jusqu'à ${studio?.max_pages ?? 24} pages par épisode.`],
          ] as const).map(([n, t, d], i) => (
            <Revele as="li" key={n} delai={i * 0.15} className="relative rounded-[8px] border-2 border-encre bg-bulle p-6 shadow-ink">
              <span className="tabular absolute right-5 top-4 text-[40px] font-bold leading-none text-trait">0{n}</span>
              <IconeEtape n={n} />
              <h3 className="mt-4 font-display text-[22px] leading-[28px]">{t}</h3>
              <p className="mt-3 text-encre-douce">{d}</p>
            </Revele>
          ))}
        </ol>
      </section>

      {/* ───── Les styles ───── */}
      <section className="mx-auto max-w-[1200px] px-4 pb-20 sm:px-6">
        <Titre sur="Cinq styles" sous="Du combat épique au conte pour enfants, et un style né ici : l'afro-manga.">Choisissez votre trait</Titre>
        <ul className="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-5">
          {STYLES_MANGA.map((st, i) => (
            <Revele as="li" key={st.id} delai={i * 0.08}>
              <Link to="/styles" hash={st.id} className="group block">
                <div className="relative">
                  <VignetteStyle style={st} legende className="aspect-[2/3] w-full shadow-ink transition-transform group-hover:-translate-y-1" />
                  {st.nouveau && <span className="absolute -right-2 -top-3 rotate-6 rounded-[4px] border-2 border-encre bg-soleil px-2 py-0.5 text-[12px] font-bold">Nouveau</span>}
                </div>
                <p className="mt-3 font-display text-[20px] leading-[26px]">{st.nom}</p>
                <p className="text-[14px] leading-5 text-encre-douce">{st.accroche}</p>
              </Link>
            </Revele>
          ))}
        </ul>
        <p className="mt-8 text-center"><Link to="/styles" className="font-bold text-indigo underline">Comparer les styles en détail</Link></p>
      </section>

      {/* ───── Ce qui est inclus ───── */}
      <section className="border-y-2 border-encre bg-encre text-papier">
        <div className="mx-auto grid max-w-[1200px] gap-8 px-4 py-14 sm:grid-cols-2 sm:px-6 lg:grid-cols-4">
          {[
            [`${studio?.max_pages ?? 24}`, "pages par épisode", "avec le plan Studio"],
            [`${studio?.max_characters ?? 10}`, "personnages par épisode", "visages gardés d'une page à l'autre"],
            ["FR · EN", "bulles lettrées", "dans la langue de votre série"],
            ["Mobile money", "pour payer", "MTN et Orange, en FCFA"],
          ].map(([chiffre, quoi, detail], i) => (
            <Revele key={quoi} delai={i * 0.1}>
              <p className="font-display text-[40px] leading-[46px] text-soleil">{chiffre}</p>
              <p className="mt-1 text-[18px] font-bold">{quoi}</p>
              <p className="text-[14px] text-[#b5ad9c]">{detail}</p>
            </Revele>
          ))}
        </div>
      </section>

      {/* ───── Galerie « À lire » ───── */}
      {semaine.length > 0 ? (
        <SectionGalerie sur="À lire" titre="Les plus aimées de la semaine" items={semaine} tri="semaine" />
      ) : recentes.length > 0 && (
        // Pas encore de « j'aime » cette semaine : on montre les dernières histoires publiées.
        <SectionGalerie sur="À lire" titre="Les dernières histoires publiées" items={recentes} tri="recentes" />
      )}
      {coups.length > 0 && (
        <SectionGalerie sur="Choisies par l'équipe" titre="Coups de cœur" items={coups} tri="coups" />
      )}

      {/* ───── Avis ───── */}
      {avis.length > 0 && (
        <section className="mx-auto max-w-[1200px] px-4 pt-20 sm:px-6">
          <Titre sur="Ils nous font confiance">Ce qu'en disent nos auteurs</Titre>
          {/* Centré : un ou deux avis au lancement ne restent pas collés à gauche. */}
          <ul className="flex flex-wrap justify-center gap-x-6 gap-y-10 [&>li]:w-full md:[&>li]:w-[calc(50%-12px)] lg:[&>li]:w-[calc(33.333%-16px)]">
            {avis.map((a, i) => <CarteAvis key={a.nom + i} avis={a} delai={(i % 3) * 0.15} />)}
          </ul>
        </section>
      )}

      {/* ───── Tarifs ───── */}
      <section id="tarifs" className="mx-auto max-w-[1200px] scroll-mt-24 px-4 py-20 sm:px-6">
        <Titre sur="Tarifs" sous="1 crédit = 1 image livrée. Les crédits réservés pour un épisode interrompu vous sont rendus.">Commencez gratuitement</Titre>
        {plans && (
          <ul className="grid gap-6 md:grid-cols-3">
            {plans.plans.map((p, i) => {
              const vedette = p.id === "creator";
              return (
                <Revele as="li" key={p.id} delai={i * 0.12}
                  className={cn("flex flex-col rounded-[8px] border-2 border-encre bg-bulle p-6", vedette ? "shadow-ink-lg md:-translate-y-2" : "shadow-ink")}>
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="font-display text-[24px] leading-[30px]">{p.name}</h3>
                    {vedette && <span className="rounded-full border-2 border-encre bg-soleil px-3 py-0.5 text-[12px] font-bold">Recommandé</span>}
                  </div>
                  <p className="mt-4"><span className="tabular text-[32px] font-bold">{p.price_xaf ? fcfa(p.price_xaf) : "Gratuit"}</span>{p.price_xaf > 0 && <span className="text-encre-douce"> / mois</span>}</p>
                  <ul className="mt-6 flex flex-1 flex-col gap-2 text-[15px]">
                    {[`${p.credits} crédits${p.price_xaf ? " par mois" : " offerts"}`, `Jusqu'à ${p.max_pages} pages par épisode`, `Jusqu'à ${p.max_characters} personnages`,
                      p.color ? "Noir et blanc ou couleur" : "Noir et blanc", ...(p.redraw ? ["Redessiner une page"] : [])].map((l) => (
                      <li key={l} className="flex gap-2"><Check size={20} strokeWidth={2.5} className="mt-0.5 shrink-0 text-succes" aria-hidden />{l}</li>
                    ))}
                  </ul>
                  <Link to="/inscription" className={cn(btnClass(vedette ? "primary" : "secondary"), "mt-6 justify-center")}>
                    {p.price_xaf ? `Choisir ${p.name}` : "Commencer gratuitement"}
                  </Link>
                </Revele>
              );
            })}
          </ul>
        )}
        {plans && (() => {
          const packs = plans.packs ?? [{ id: "pack", ...plans.pack }];
          const petit = packs[0]!;
          return <p className="mt-8 text-center text-encre-douce">Besoin de plus ? Des packs de <b>{packs.map((p) => p.credits).join(", ").replace(/, (\d+)$/, " ou $1")} crédits</b>, dès <b>{fcfa(petit.price_xaf)}</b>, sans date d'expiration.</p>;
        })()}
      </section>

      {/* ───── Appel final ───── */}
      <section className="relative overflow-hidden border-t-2 border-encre bg-vermillon text-sur-vermillon">
        <div className="vitesse pointer-events-none absolute inset-0" aria-hidden />
        <Revele className="relative mx-auto max-w-[900px] px-4 py-20 text-center sm:px-6">
          <h2 className="font-display text-[36px] leading-[42px] sm:text-[52px] sm:leading-[58px]">Le premier chapitre commence par une idée.</h2>
          <p className="mx-auto mt-4 max-w-xl text-[18px] leading-7">Écrivez-la, on s'occupe du dessin.</p>
          <Link to="/inscription" className="mt-8 inline-flex min-h-12 items-center rounded-[4px] border-2 border-encre bg-bulle px-6 font-bold text-encre shadow-ink transition-transform hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-ink-sm">
            Créer mon premier épisode
          </Link>
        </Revele>
      </section>

    </div>
  );
}

function SectionGalerie({ sur, titre, items, tri }: { sur: string; titre: string; items: PageGalerie["items"]; tri: TriGalerie }) {
  return (
    <section className="mx-auto max-w-[1200px] px-4 pt-20 sm:px-6">
      <Titre sur={sur} sous="Des chapitres créés par nos auteurs, à lire gratuitement.">{titre}</Titre>
      <ul className="flex flex-wrap justify-center gap-6 [&>li]:w-full sm:[&>li]:w-[calc(50%-12px)] lg:[&>li]:w-[calc(25%-18px)]">
        {items.map((c, i) => <Revele as="li" key={c.id} delai={i * 0.1}><CarteHistoire c={c} semaine={tri === "semaine"} /></Revele>)}
      </ul>
      <p className="mt-8 text-center"><Link to="/galerie" search={{ tri }} className="font-bold text-indigo underline">Voir toute la galerie</Link></p>
    </section>
  );
}

function BandeauPartenaires({ items }: { items: Partenaire[] }) {
  // La liste est doublée pour boucler sans saut ; la copie est cachée aux lecteurs d'écran.
  const piste = (copie: boolean) => (
    <ul className="flex shrink-0 items-center gap-16 pr-16" aria-hidden={copie || undefined}>
      {items.map((p, i) => (
        <li key={p.nom + i} className="shrink-0">
          {(() => {
            const contenu = p.logo
              ? <img src={p.logo} alt={copie ? "" : p.nom} className="h-10 w-auto max-w-[180px] object-contain opacity-70 grayscale transition hover:opacity-100 hover:grayscale-0" />
              : <span className="font-display text-[22px] leading-none text-encre-douce">{p.nom}</span>;
            return p.lien && !copie ? <a href={p.lien} target="_blank" rel="noreferrer">{contenu}</a> : contenu;
          })()}
        </li>
      ))}
    </ul>
  );
  return (
    <section aria-label="Ils nous font confiance" className="border-y-2 border-encre bg-bulle py-8">
      <p className="label-caps mb-6 text-center">Ils nous font confiance</p>
      <div className="defilement overflow-hidden">
        <div className="defilement-piste flex w-max" style={{ "--duree": `${Math.max(20, items.length * 5)}s` } as CSSProperties}>
          {piste(false)}{piste(true)}
        </div>
      </div>
    </section>
  );
}

function CarteAvis({ avis, delai }: { avis: Avis; delai: number }) {
  const initiales = avis.nom.split(/\s+/).map((m) => m[0]).join("").slice(0, 2).toUpperCase();
  return (
    <Revele as="li" delai={delai} className="flex flex-col">
      <figure className="m-0 flex h-full flex-col">
        <blockquote className="relative flex-1 rounded-[20px] border-2 border-encre bg-bulle p-6 shadow-ink">
          {avis.note && (
            <p className="mb-3 flex gap-0.5" aria-label={`${avis.note} sur 5`}>
              {Array.from({ length: 5 }, (_, i) => <Star key={i} size={18} strokeWidth={2} aria-hidden className={i < avis.note! ? "fill-soleil text-encre" : "text-trait"} />)}
            </p>
          )}
          <p className="text-[17px] leading-7">« {avis.texte} »</p>
          {/* queue de bulle */}
          <svg viewBox="0 0 40 24" className="absolute -bottom-[22px] left-10 h-6 w-10" aria-hidden>
            <path d="M0,0 L14,22 L30,0" fill="var(--bulle)" stroke="var(--encre)" strokeWidth="2" strokeLinejoin="round" />
            <path d="M2,0 H28" stroke="var(--bulle)" strokeWidth="4" />
          </svg>
        </blockquote>
        <figcaption className="mt-7 flex items-center gap-3 pl-2">
          {avis.photo
            ? <img src={avis.photo} alt="" className="size-12 rounded-full border-2 border-encre object-cover" />
            : <span className="flex size-12 items-center justify-center rounded-full border-2 border-encre bg-soleil font-bold" aria-hidden>{initiales}</span>}
          <span><span className="block font-bold">{avis.nom}</span><span className="block text-[14px] text-encre-douce">{avis.role}</span></span>
        </figcaption>
      </figure>
    </Revele>
  );
}

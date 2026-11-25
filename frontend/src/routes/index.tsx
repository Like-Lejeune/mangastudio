import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { api, type SeriesItem } from "@/lib/api";
import { useMe, useToken } from "@/lib/session";
import { Accueil } from "@/components/accueil/Accueil";
import { ApercuGalerie } from "@/components/galerie/ApercuGalerie";
import { BandeauConcours } from "@/components/BandeauConcours";
import { styleParId, stylesManga } from "@/content/styles";
import { getLang, tr } from "@/lib/i18n";
import { VignetteStyle } from "@/components/StyleManga";
import { Button, Card, Container, ErrorNote, Field, PageTitle, RequireAuth, Textarea } from "@/components/ink";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/")({
  // ?style=afro : la page « Styles » pré-sélectionne le style choisi.
  validateSearch: (search: Record<string, unknown>): { style?: string } => (typeof search.style === "string" ? { style: search.style } : {}),
  head: () => ({
    meta: [
      { title: tr("MangaStudio — Vos idées deviennent des épisodes de manga", "MangaStudio — Your ideas become manga episodes") },
      { name: "description", content: tr("Décrivez une idée, ajoutez vos personnages : MangaStudio dessine vos épisodes de manga, page après page.", "Describe an idea, add your characters: MangaStudio draws your manga episodes, page after page.") },
      { property: "og:title", content: tr("MangaStudio — Vos idées deviennent des épisodes de manga", "MangaStudio — Your ideas become manga episodes") },
      { property: "og:description", content: tr("Un studio en ligne qui transforme une idée et des personnages en épisodes de manga.", "An online studio that turns an idea and characters into manga episodes.") },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

function Index() {
  const token = useToken();
  if (token === undefined) return null;
  return token ? <RequireAuth><MesSeries /></RequireAuth> : <Accueil />;
}


function Choice({ name, value, current, onChange, label, disabled, note }: { name: string; value: string; current: string; onChange: (v: string) => void; label: string; disabled?: boolean; note?: string | undefined }) {
  const on = current === value;
  return (
    <label className={cn("flex min-h-11 cursor-pointer items-center gap-2 rounded-[4px] border-2 border-encre px-3 py-2 font-bold", on ? "bg-vermillon text-sur-vermillon" : "bg-bulle", disabled && "cursor-not-allowed opacity-50")}>
      <input type="radio" name={name} value={value} checked={on} disabled={disabled} onChange={() => onChange(value)} className="size-4 accent-current" />
      {label}{note && <span className="text-[12px] font-medium">({note})</span>}
    </label>
  );
}

function MesSeries() {
  const { data, isLoading, error } = useQuery({ queryKey: ["series"], queryFn: () => api<SeriesItem[] | { series: SeriesItem[] }>("/series") });
  const list = Array.isArray(data) ? data : data?.series ?? [];
  const { data: me } = useMe();
  const qc = useQueryClient();
  const nav = useNavigate();
  const [idea, setIdea] = useState("");
  const { style: styleDemande } = Route.useSearch();
  const [style, setStyle] = useState(styleDemande && styleParId(styleDemande) ? styleDemande : "shonen");
  const [render, setRender] = useState("bw");
  const [lang, setLang] = useState<string>(getLang());       // langue des bulles : celle du site par défaut
  const create = useMutation({
    mutationFn: () => api<{ id: string }>("/series", { body: { premise: idea, style, palette: render, language: lang } }),
    onSuccess: (s) => { qc.invalidateQueries({ queryKey: ["series"] }); nav({ to: "/series/$id", params: { id: String(s.id) } }); },
  });
  const blocked = (create.error as { code?: string } | null)?.code === "blocked_terms";
  const tooShort = idea.trim().length < 8;

  return (
    <Container>
      <PageTitle sub={me ? tr(`Bonjour ${me.display_name}, voici vos séries.`, `Hello ${me.display_name}, here are your series.`) : undefined}>{tr("Mes séries", "My series")}</PageTitle>
      <BandeauConcours className="mb-8" />
      {!!me?.weekly_refill && (
        <p role="status" className="mb-6 rounded-[4px] border-2 border-encre bg-soleil px-4 py-3 font-bold">
          {tr(`Recharge de la semaine : +${me.weekly_refill} crédits. `, `Weekly top-up: +${me.weekly_refill} credits. `)}<Link to="/gagner" className="underline">{tr("Gagner plus de crédits", "Earn more credits")}</Link>
        </p>
      )}
      <div className="grid gap-8 lg:grid-cols-[1fr_380px]">
        <section aria-label={tr("Vos séries", "Your series")}>
          {isLoading && <p className="text-encre-douce">{tr("Chargement de vos séries…", "Loading your series…")}</p>}
          <ErrorNote error={error} />
          {!isLoading && !error && list.length === 0 && (
            <Card><p>{tr("Vous n'avez encore aucune série. Décrivez votre idée dans le formulaire pour commencer.", "You don't have any series yet. Describe your idea in the form to get started.")}</p></Card>
          )}
          <ul className="grid grid-cols-2 gap-6 sm:grid-cols-3">
            {list.map((s) => (
              <li key={s.id}>
                <Link to="/series/$id" params={{ id: String(s.id) }} className="group block rounded-[8px] border-2 border-encre bg-bulle p-3 shadow-ink transition-transform hover:translate-x-[2px] hover:translate-y-[2px]">
                  {s.cover_url ? <img src={s.cover_url} alt="" className="aspect-[2/3] w-full border-2 border-encre object-cover" /> : <div className="trame aspect-[2/3] w-full border-2 border-encre" aria-hidden />}
                  <h2 className="mt-3 font-bold leading-6">{s.title}</h2>
                  <p className="line-clamp-2 text-[14px] leading-5 text-encre-douce">{s.premise}</p>
                </Link>
              </li>
            ))}
          </ul>
        </section>
        <Card featured className="h-fit">
          <h2 className="font-display text-[24px] leading-[30px]">{tr("Nouvelle série", "New series")}</h2>
          <form className="mt-6 flex flex-col gap-6" onSubmit={(e) => { e.preventDefault(); if (!tooShort) create.mutate(); }}>
            <Field label={tr("Votre idée", "Your idea")} htmlFor="idea" hint={<>
              <p className="text-right text-[12px] text-encre-douce"><span className="tabular">{idea.length}</span> / <span className="tabular">1500</span></p>
              {blocked && <ErrorNote inline error={create.error} />}
            </>}>
              <Textarea id="idea" required minLength={8} maxLength={1500} value={idea} onChange={(e) => setIdea(e.target.value)} placeholder={tr("Une lycéenne découvre que son chat garde le portail entre deux mondes…", "A schoolgirl discovers her cat guards the gate between two worlds…")} aria-invalid={blocked} />
            </Field>
            <fieldset className="flex flex-col gap-2">
              <legend className="label-caps mb-2">{tr("Style", "Style")}</legend>
              <div className="flex flex-col gap-2">
                {stylesManga().map((s) => {
                  const on = style === s.id;
                  return (
                    <label key={s.id} className={cn("flex cursor-pointer items-center gap-3 rounded-[4px] border-2 border-encre p-2", on ? "bg-vermillon text-sur-vermillon" : "bg-bulle hover:bg-papier")}>
                      <input type="radio" name="style" value={s.id} checked={on} onChange={() => setStyle(s.id)} className="sr-only" />
                      <VignetteStyle style={s} className="aspect-[2/3] w-12 shrink-0" />
                      <span className="min-w-0">
                        <span className="flex items-center gap-2 font-bold">{s.nom}{s.nouveau && <span className="rounded-full bg-soleil px-2 text-[11px] text-encre">{tr("Nouveau", "New")}</span>}</span>
                        <span className={cn("block text-[13px] leading-5", on ? "text-sur-vermillon" : "text-encre-douce")}>{s.accroche}</span>
                      </span>
                    </label>
                  );
                })}
              </div>
              <Link to="/styles" target="_blank" className="mt-1 self-start text-[14px] font-bold text-indigo underline">{tr("Voir les styles en détail (nouvel onglet)", "See the styles in detail (new tab)")}</Link>
            </fieldset>
            <fieldset><legend className="label-caps mb-2">{tr("Rendu", "Rendering")}</legend>
              <div className="grid grid-cols-2 gap-2">
                <Choice name="render" value="bw" label={tr("Noir et blanc", "Black & white")} current={render} onChange={setRender} />
                <Choice name="render" value="color" label={tr("Couleur", "Colour")} current={render} onChange={setRender} disabled={!me?.plan.color} note={!me?.plan.color ? tr("non inclus", "not included") : undefined} />
              </div>
            </fieldset>
            <fieldset><legend className="label-caps mb-2">{tr("Langue des bulles", "Balloon language")}</legend>
              <div className="grid grid-cols-2 gap-2">
                <Choice name="lang" value="fr" label={tr("Français", "French")} current={lang} onChange={setLang} />
                <Choice name="lang" value="en" label={tr("Anglais", "English")} current={lang} onChange={setLang} />
              </div>
            </fieldset>
            {!blocked && <ErrorNote error={create.error} />}
            <Button type="submit" variant="primary" disabled={create.isPending || tooShort}><Plus size={20} strokeWidth={2} aria-hidden />{create.isPending ? tr("Création…", "Creating…") : tr("Créer la série", "Create the series")}</Button>
          </form>
        </Card>
      </div>
      <ApercuGalerie />
    </Container>
  );
}

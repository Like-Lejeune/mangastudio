import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { api, type SeriesItem } from "@/lib/api";
import { useMe, useToken } from "@/lib/session";
import { Accueil } from "@/components/accueil/Accueil";
import { STYLES_MANGA, styleParId } from "@/content/styles";
import { VignetteStyle } from "@/components/StyleManga";
import { Button, Card, Container, ErrorNote, Field, PageTitle, RequireAuth, Textarea } from "@/components/ink";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/")({
  // ?style=afro : la page « Styles » pré-sélectionne le style choisi.
  validateSearch: (search: Record<string, unknown>): { style?: string } => (typeof search.style === "string" ? { style: search.style } : {}),
  head: () => ({
    meta: [
      { title: "MangaStudio — Vos idées deviennent des épisodes de manga" },
      { name: "description", content: "Décrivez une idée, ajoutez vos personnages : MangaStudio dessine vos épisodes de manga, page après page." },
      { property: "og:title", content: "MangaStudio — Vos idées deviennent des épisodes de manga" },
      { property: "og:description", content: "Un studio en ligne qui transforme une idée et des personnages en épisodes de manga." },
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
  const [lang, setLang] = useState("fr");
  const create = useMutation({
    mutationFn: () => api<{ id: string }>("/series", { body: { premise: idea, style, palette: render, language: lang } }),
    onSuccess: (s) => { qc.invalidateQueries({ queryKey: ["series"] }); nav({ to: "/series/$id", params: { id: String(s.id) } }); },
  });
  const blocked = (create.error as { code?: string } | null)?.code === "blocked_terms";
  const tooShort = idea.trim().length < 8;

  return (
    <Container>
      <PageTitle sub={me ? `Bonjour ${me.display_name}, voici vos séries.` : undefined}>Mes séries</PageTitle>
      <div className="grid gap-8 lg:grid-cols-[1fr_380px]">
        <section aria-label="Vos séries">
          {isLoading && <p className="text-encre-douce">Chargement de vos séries…</p>}
          <ErrorNote error={error} />
          {!isLoading && !error && list.length === 0 && (
            <Card><p>Vous n'avez encore aucune série. Décrivez votre idée dans le formulaire pour commencer.</p></Card>
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
          <h2 className="font-display text-[24px] leading-[30px]">Nouvelle série</h2>
          <form className="mt-6 flex flex-col gap-6" onSubmit={(e) => { e.preventDefault(); if (!tooShort) create.mutate(); }}>
            <Field label="Votre idée" htmlFor="idea" hint={<>
              <p className="text-right text-[12px] text-encre-douce"><span className="tabular">{idea.length}</span> / <span className="tabular">1500</span></p>
              {blocked && <ErrorNote inline error={create.error} />}
            </>}>
              <Textarea id="idea" required minLength={8} maxLength={1500} value={idea} onChange={(e) => setIdea(e.target.value)} placeholder="Une lycéenne découvre que son chat garde le portail entre deux mondes…" aria-invalid={blocked} />
            </Field>
            <fieldset className="flex flex-col gap-2">
              <legend className="label-caps mb-2">Style</legend>
              <div className="flex flex-col gap-2">
                {STYLES_MANGA.map((s) => {
                  const on = style === s.id;
                  return (
                    <label key={s.id} className={cn("flex cursor-pointer items-center gap-3 rounded-[4px] border-2 border-encre p-2", on ? "bg-vermillon text-sur-vermillon" : "bg-bulle hover:bg-papier")}>
                      <input type="radio" name="style" value={s.id} checked={on} onChange={() => setStyle(s.id)} className="sr-only" />
                      <VignetteStyle style={s} className="aspect-[2/3] w-12 shrink-0" />
                      <span className="min-w-0">
                        <span className="flex items-center gap-2 font-bold">{s.nom}{s.nouveau && <span className="rounded-full bg-soleil px-2 text-[11px] text-encre">Nouveau</span>}</span>
                        <span className={cn("block text-[13px] leading-5", on ? "text-sur-vermillon" : "text-encre-douce")}>{s.accroche}</span>
                      </span>
                    </label>
                  );
                })}
              </div>
              <Link to="/styles" target="_blank" className="mt-1 self-start text-[14px] font-bold text-indigo underline">Voir les styles en détail (nouvel onglet)</Link>
            </fieldset>
            <fieldset><legend className="label-caps mb-2">Rendu</legend>
              <div className="grid grid-cols-2 gap-2">
                <Choice name="render" value="bw" label="Noir et blanc" current={render} onChange={setRender} />
                <Choice name="render" value="color" label="Couleur" current={render} onChange={setRender} disabled={!me?.plan.color} note={!me?.plan.color ? "non inclus" : undefined} />
              </div>
            </fieldset>
            <fieldset><legend className="label-caps mb-2">Langue</legend>
              <div className="grid grid-cols-2 gap-2">
                <Choice name="lang" value="fr" label="Français" current={lang} onChange={setLang} />
                <Choice name="lang" value="en" label="Anglais" current={lang} onChange={setLang} />
              </div>
            </fieldset>
            {!blocked && <ErrorNote error={create.error} />}
            <Button type="submit" variant="primary" disabled={create.isPending || tooShort}><Plus size={20} strokeWidth={2} aria-hidden />{create.isPending ? "Création…" : "Créer la série"}</Button>
          </form>
        </Card>
      </div>
    </Container>
  );
}

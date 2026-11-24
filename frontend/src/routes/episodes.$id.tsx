import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Check, ChevronLeft, ChevronRight, Loader, Maximize2, RotateCcw, X } from "lucide-react";
import { api, ACTIVE, STATUS_LABEL, type Episode } from "@/lib/api";
import { useMe } from "@/lib/session";
import { Button, Card, Container, ErrorNote, Field, PageTitle, Pill, RequireAuth, Textarea } from "@/components/ink";
import { cn } from "@/lib/utils";
import { DonnerAvis } from "@/components/DonnerAvis";
import { PartagerChapitre } from "@/components/PartagerChapitre";

export const Route = createFileRoute("/episodes/$id")({
  head: () => ({
    meta: [
      { title: "Lecture de l'épisode — MangaStudio" },
      { name: "description", content: "Suivez le dessin de votre épisode page après page et lisez-le." },
      { property: "og:title", content: "Lecture de l'épisode — MangaStudio" },
      { property: "og:description", content: "Suivez le dessin de votre épisode page après page." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => <RequireAuth><EpisodePage /></RequireAuth>,
});

const STAGE_LABEL: Record<string, string> = {
  design: "Design des personnages", script: "Scénario", moderation: "Modération", sheet: "Fiches modèles",
  page: "Pages", check: "Relecture", cover: "Couverture", redraw: "Redessins demandés",
};
const STAGE_ORDER = Object.keys(STAGE_LABEL);   // ordre du pipeline, pas ordre alphabétique
const STEPS = [["designing", "Design des personnages"], ["writing", "Écriture du scénario"], ["moderating", "Vérification du contenu"], ["drawing", "Dessin des pages"]] as const;
const fmt = (n: number | undefined) => (n ?? 0).toLocaleString("fr-FR");

function EpisodePage() {
  const { id } = Route.useParams();
  const qc = useQueryClient();
  const { data: me } = useMe();
  const [redrawing, setRedrawing] = useState<{ pageId: string; attempts: number; at: number } | null>(null);
  const { data: ep, error, isLoading } = useQuery({
    queryKey: ["episode", id],
    queryFn: () => api<Episode>(`/episodes/${id}`),
    // On interroge l'API pendant la génération, et pendant un redessin demandé.
    refetchInterval: (q) => ((q.state.data && ACTIVE.includes(q.state.data.status)) || redrawing ? 2000 : false),
  });
  // Un redessin se termine quand le compteur de tentatives de la page augmente.
  useEffect(() => {
    if (!redrawing) return;
    const p = ep?.pages.find((x) => String(x.id) === redrawing.pageId);
    const over = Date.now() - redrawing.at > 3 * 60 * 1000;
    if ((p && (p.attempts ?? 0) > redrawing.attempts) || over) { setRedrawing(null); qc.invalidateQueries({ queryKey: ["me"] }); }
  }, [ep, redrawing, qc]);
  const prev = useRef<string | undefined>(undefined);
  useEffect(() => {
    if (!ep) return;
    if (prev.current && ACTIVE.includes(prev.current) && !ACTIVE.includes(ep.status)) qc.invalidateQueries({ queryKey: ["me"] });
    prev.current = ep.status;
  }, [ep?.status, ep, qc]);
  const [current, setCurrent] = useState(0);
  const [reader, setReader] = useState(false);
  const resume = useMutation({
    mutationFn: () => api(`/episodes/${id}/resume`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["episode", id] }),
  });

  if (isLoading) return <Container><p className="text-encre-douce">Chargement de l'épisode…</p></Container>;
  if (error || !ep) return <Container><ErrorNote error={error ?? new Error("Épisode introuvable.")} /></Container>;

  const pages = [...(ep.pages ?? [])].sort((a, b) => a.number - b.number);
  const total = ep.page_count || pages.length;
  const drawn = pages.filter((p) => p.url).length;
  const active = ACTIVE.includes(ep.status);
  const stepIdx = STEPS.findIndex(([k]) => k === ep.status);
  const finished = ep.status === "done";
  const page = pages[Math.min(current, Math.max(0, pages.length - 1))];

  return (
    <Container>
      {ep.series_id && <Link to="/series/$id" params={{ id: String(ep.series_id) }} className="mb-4 inline-flex min-h-11 items-center font-bold text-indigo underline">Retour à la série</Link>}
      <PageTitle sub={<span className="inline-flex flex-wrap items-center gap-2">Statut : <Pill tone={finished ? "succes" : active ? "indigo" : "alerte"}>{STATUS_LABEL[ep.status] ?? ep.status}</Pill></span>}>
        {ep.title || `Épisode ${ep.number}`}
      </PageTitle>

      <ol className="mb-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4" aria-label="Étapes">
        {STEPS.map(([key, label], i) => {
          const done = finished || (active && ep.status !== "queued" && i < stepIdx);
          const now = i === stepIdx;
          const state = done ? "Terminé" : now ? "En cours" : "À venir";
          return (
            <li key={key} className={cn("flex items-center gap-3 rounded-[8px] border-2 border-encre bg-bulle p-3", now ? "shadow-ink-lg" : "shadow-ink")}>
              <span className={cn("flex size-8 shrink-0 items-center justify-center rounded-full border-2 border-encre", done && "bg-succes text-bulle")}>
                {done ? <Check size={18} strokeWidth={2} aria-hidden /> : now ? <Loader size={18} strokeWidth={2} className="animate-spin" aria-hidden /> : <span className="tabular text-[13px] font-bold">{i + 1}</span>}
              </span>
              <span className="leading-5">
                <span className="block font-bold">{label}{key === "drawing" && <> <span className="tabular">{drawn}</span> sur <span className="tabular">{total}</span></>}</span>
                <span className={cn("text-[13px] font-bold", done ? "text-succes" : "text-encre-douce")}>{state}</span>
              </span>
            </li>
          );
        })}
      </ol>

      {ep.status === "blocked" && (
        <Card className="mb-8 border-alerte"><p className="font-display text-[24px] leading-[30px] text-alerte">Épisode refusé par la modération</p>
          {ep.error && <p className="mt-2">{ep.error}</p>}<p className="mt-2 font-bold">Aucun crédit n'a été débité.</p></Card>
      )}
      {ep.status === "failed" && (
        <Card className="mb-8"><p className="font-bold text-alerte">L'épisode s'est interrompu.</p>{ep.error && <p className="mt-2">{ep.error}</p>}
          <ErrorNote error={resume.error} />
          <Button className="mt-4" variant="primary" disabled={resume.isPending} onClick={() => resume.mutate()}><RotateCcw size={20} strokeWidth={2} aria-hidden />Reprendre</Button></Card>
      )}

      <div className="grid gap-8 lg:grid-cols-[1fr_280px]">
        <section aria-label="Page sélectionnée">
          <PageView url={page?.url} number={page?.number ?? 1} failed={page?.status === "failed"} big />
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <Button aria-label="Page précédente" disabled={current <= 0} onClick={() => setCurrent((c) => c - 1)}><ChevronLeft size={20} strokeWidth={2} aria-hidden /></Button>
            <span className="tabular font-bold">Page {page?.number ?? 1} / {total}</span>
            <Button aria-label="Page suivante" disabled={current >= pages.length - 1} onClick={() => setCurrent((c) => c + 1)}><ChevronRight size={20} strokeWidth={2} aria-hidden /></Button>
            <Button className="ml-auto" disabled={drawn === 0} onClick={() => setReader(true)}><Maximize2 size={20} strokeWidth={2} aria-hidden />Plein écran</Button>
          </div>
          {redrawing && <p role="status" className="mt-4 font-bold text-indigo">Redessin en cours…</p>}
          {me?.plan.redraw && page && (page.url || page.status === "failed") && !active && ep.status !== "blocked" && !redrawing && (
            <Redraw key={page.id} pageId={String(page.id)} onSent={() => setRedrawing({ pageId: String(page.id), attempts: page.attempts ?? 0, at: Date.now() })} />
          )}
        </section>
        <aside aria-label="Toutes les pages">
          <ul className="grid grid-cols-3 gap-3 lg:grid-cols-2">
            {pages.map((p, i) => (
              <li key={p.id}>
                <button onClick={() => setCurrent(i)} aria-current={i === current} aria-label={`Page ${p.number}${p.url ? "" : p.status === "failed" ? ", à refaire" : ", en cours"}`} className={cn("block w-full", i === current && "outline-3 outline-offset-2 outline-vermillon")}>
                  <PageView url={p.url} number={p.number} failed={p.status === "failed"} />
                </button>
              </li>
            ))}
          </ul>
        </aside>
      </div>

      {ep.usage && <UsageCard u={ep.usage} />}
      {finished && <PartagerChapitre ep={ep} />}
      {finished && <DonnerAvis episodeId={ep.id} compact />}
      {reader && <Reader pages={pages.filter((p) => p.url)} onClose={() => setReader(false)} />}
    </Container>
  );
}

function PageView({ url, number, big, failed }: { url?: string | null | undefined; number: number; big?: boolean; failed?: boolean }) {
  const state = failed ? "À refaire" : "En cours";
  return url ? (
    <img src={url} alt={`Page ${number}`} className={cn("aspect-[2/3] w-full border-2 border-encre bg-blanc object-contain", big && "mx-auto max-w-[560px]")} />
  ) : (
    <div className={cn("trame relative flex aspect-[2/3] w-full items-center justify-center border-2 border-encre", big && "mx-auto max-w-[560px]")}>
      <span className="rounded-full border-2 border-encre bg-bulle px-3 py-1 text-[13px] font-bold">{big ? `Page ${number} · ${state}` : state}</span>
    </div>
  );
}

function Redraw({ pageId, onSent }: { pageId: string; onSent: () => void }) {
  const [note, setNote] = useState("");
  const m = useMutation({
    mutationFn: () => api(`/pages/${pageId}/redraw`, { body: { note } }),
    onSuccess: () => { setNote(""); onSent(); },
  });
  return (
    <Card className="mt-6 max-w-[560px]">
      <form className="flex flex-col gap-4" onSubmit={(e) => { e.preventDefault(); m.mutate(); }}>
        <Field label="Remarque pour cette page" htmlFor="note" hint={(m.error as { code?: string } | null)?.code === "blocked_terms" ? <ErrorNote inline error={m.error} /> : undefined}>
          <Textarea id="note" required minLength={3} maxLength={300} value={note} onChange={(e) => setNote(e.target.value)} placeholder="Agrandir la case du milieu, regard plus déterminé…" />
        </Field>
        {(m.error as { code?: string } | null)?.code !== "blocked_terms" && <ErrorNote error={m.error} />}
        <Button type="submit" disabled={m.isPending}>Redessiner cette page · 1 crédit</Button>
      </form>
    </Card>
  );
}

function UsageCard({ u }: { u: NonNullable<Episode["usage"]> }) {
  return (
    <Card className="mt-12">
      <h2 className="font-display text-[24px] leading-[30px]">Consommation de l'épisode</h2>
      <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[["Tokens lus", u.input_tokens], ["Tokens écrits", u.output_tokens], ["Images", u.images], ["Crédits", u.credits]].map(([l, v]) => (
          <div key={l as string} className="rounded-[4px] border-2 border-encre p-3"><dt className="label-caps">{l}</dt><dd className="tabular mt-1 text-right text-[20px] font-bold">{fmt(v as number)}</dd></div>
        ))}
      </dl>
      <div className="mt-6 overflow-x-auto">
        <table className="w-full min-w-[520px] text-[14px] leading-5">
          <thead><tr className="border-b-2 border-encre text-left"><th className="label-caps py-2">Étape</th><th className="label-caps py-2 text-right">Appels</th><th className="label-caps py-2 text-right">Tokens lus</th><th className="label-caps py-2 text-right">Tokens écrits</th><th className="label-caps py-2 text-right">Images</th></tr></thead>
          <tbody>
            {[...u.stages].sort((a, b) => STAGE_ORDER.indexOf(a.stage) - STAGE_ORDER.indexOf(b.stage)).map((s) => (
              <tr key={s.stage} className="border-b border-trait">
                <td className="py-2 font-medium">{STAGE_LABEL[s.stage] ?? s.stage}</td>
                <td className="tabular py-2 text-right">{fmt(s.calls)}</td><td className="tabular py-2 text-right">{fmt(s.input_tokens)}</td>
                <td className="tabular py-2 text-right">{fmt(s.output_tokens)}</td><td className="tabular py-2 text-right">{fmt(s.images)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function Reader({ pages, onClose }: { pages: Episode["pages"]; onClose: () => void }) {
  const [i, setI] = useState(0);
  useEffect(() => {
    const k = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowRight") setI((x) => Math.min(pages.length - 1, x + 1));
      if (e.key === "ArrowLeft") setI((x) => Math.max(0, x - 1));
    };
    window.addEventListener("keydown", k); return () => window.removeEventListener("keydown", k);
  }, [pages.length, onClose]);
  const p = pages[i];
  return (
    <div className="dark fixed inset-0 z-50" role="dialog" aria-modal aria-label="Lecteur plein écran">
      <div className="flex h-full flex-col bg-papier text-encre">
        <div className="flex items-center justify-between gap-3 p-3">
          <span className="tabular font-bold">Page {p?.number} / {pages.length}</span>
          <Button aria-label="Fermer le lecteur" onClick={onClose}><X size={20} strokeWidth={2} aria-hidden /></Button>
        </div>
        <div className="flex min-h-0 flex-1 items-center justify-center gap-3 px-3 pb-6">
          <Button aria-label="Page précédente" disabled={i === 0} onClick={() => setI(i - 1)}><ChevronLeft size={20} strokeWidth={2} aria-hidden /></Button>
          {p?.url && <img src={p.url} alt={`Page ${p.number}`} className="aspect-[2/3] h-full max-h-full min-w-0 border-2 border-encre bg-blanc object-contain" />}
          <Button aria-label="Page suivante" disabled={i >= pages.length - 1} onClick={() => setI(i + 1)}><ChevronRight size={20} strokeWidth={2} aria-hidden /></Button>
        </div>
      </div>
    </div>
  );
}

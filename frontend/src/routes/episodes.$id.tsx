import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Check, ChevronLeft, ChevronRight, Loader, Maximize2, RotateCcw, Trash2, X } from "lucide-react";
import { api, ACTIVE, statusLabel, type Episode } from "@/lib/api";
import { intlLocale, tr } from "@/lib/i18n";
import { useMe } from "@/lib/session";
import { btnClass, Button, Card, Container, ErrorNote, Field, PageTitle, Pill, RequireAuth, Textarea } from "@/components/ink";
import { cn } from "@/lib/utils";
import { DonnerAvis } from "@/components/DonnerAvis";
import { PartagerChapitre } from "@/components/PartagerChapitre";
import { PublierChapitre } from "@/components/PublierChapitre";

export const Route = createFileRoute("/episodes/$id")({
  head: () => ({
    meta: [
      { title: tr("Lecture de l'épisode — MangaStudio", "Episode — MangaStudio") },
      { name: "description", content: tr("Suivez le dessin de votre épisode page après page et lisez-le.", "Follow your episode being drawn page by page, and read it.") },
      { property: "og:title", content: tr("Lecture de l'épisode — MangaStudio", "Episode — MangaStudio") },
      { property: "og:description", content: tr("Suivez le dessin de votre épisode page après page.", "Follow your episode being drawn page by page.") },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => <RequireAuth><EpisodePage /></RequireAuth>,
});

const stageLabel = (s: string) => ({
  design: tr("Design des personnages", "Character design"), script: tr("Scénario", "Script"), moderation: tr("Modération", "Moderation"),
  sheet: tr("Fiches modèles", "Model sheets"), page: tr("Pages", "Pages"), check: tr("Relecture", "Review"),
  cover: tr("Couverture", "Cover"), redraw: tr("Redessins demandés", "Requested redraws"),
} as Record<string, string>)[s] ?? s;
const STAGE_ORDER = ["design", "script", "moderation", "sheet", "page", "check", "cover", "redraw"];   // ordre du pipeline
const steps = () => [["designing", tr("Design des personnages", "Character design")], ["writing", tr("Écriture du scénario", "Writing the script")],
  ["moderating", tr("Vérification du contenu", "Checking content")], ["drawing", tr("Dessin des pages", "Drawing pages")]] as const;
const fmt = (n: number | undefined) => (n ?? 0).toLocaleString(intlLocale());

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
  const abandon = useMutation({
    mutationFn: () => api(`/episodes/${id}/abandon`, { method: "POST" }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["episode", id] }); qc.invalidateQueries({ queryKey: ["series"] }); qc.invalidateQueries({ queryKey: ["me"] }); },
  });
  const navigate = useNavigate();
  const effacer = useMutation({
    mutationFn: () => api<{ series_id: string }>(`/episodes/${id}`, { method: "DELETE" }),
    onSuccess: (r) => {
      qc.removeQueries({ queryKey: ["episode", id] });
      qc.invalidateQueries({ queryKey: ["series"] });
      navigate({ to: "/series/$id", params: { id: String(r.series_id) } });
    },
  });
  const resume = useMutation({
    mutationFn: () => api(`/episodes/${id}/resume`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["episode", id] }),
  });

  if (isLoading) return <Container><p className="text-encre-douce">{tr("Chargement de l'épisode…", "Loading the episode…")}</p></Container>;
  if (error || !ep) return <Container><ErrorNote error={error ?? new Error(tr("Épisode introuvable.", "Episode not found."))} /></Container>;
  const STEPS = steps();

  const pages = [...(ep.pages ?? [])].sort((a, b) => a.number - b.number);
  const total = ep.page_count || pages.length;
  const drawn = pages.filter((p) => p.url).length;
  const active = ACTIVE.includes(ep.status);
  const stepIdx = STEPS.findIndex(([k]) => k === ep.status);
  const finished = ep.status === "done";
  const page = pages[Math.min(current, Math.max(0, pages.length - 1))];

  return (
    <Container>
      {ep.series_id && <Link to="/series/$id" params={{ id: String(ep.series_id) }} className="mb-4 inline-flex min-h-11 items-center font-bold text-indigo underline">{tr("Retour à la série", "Back to the series")}</Link>}
      <PageTitle sub={<span className="inline-flex flex-wrap items-center gap-2">{tr("Statut : ", "Status: ")}<Pill tone={finished ? "succes" : active ? "indigo" : "alerte"}>{statusLabel(ep.status)}</Pill></span>}>
        {ep.title || tr(`Épisode ${ep.number}`, `Episode ${ep.number}`)}
      </PageTitle>

      <ol className="mb-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4" aria-label={tr("Étapes", "Steps")}>
        {STEPS.map(([key, label], i) => {
          const done = finished || (active && ep.status !== "queued" && i < stepIdx);
          const now = i === stepIdx;
          const state = done ? tr("Terminé", "Done") : now ? tr("En cours", "In progress") : tr("À venir", "Coming up");
          return (
            <li key={key} className={cn("flex items-center gap-3 rounded-[8px] border-2 border-encre bg-bulle p-3", now ? "shadow-ink-lg" : "shadow-ink")}>
              <span className={cn("flex size-8 shrink-0 items-center justify-center rounded-full border-2 border-encre", done && "bg-succes text-bulle")}>
                {done ? <Check size={18} strokeWidth={2} aria-hidden /> : now ? <Loader size={18} strokeWidth={2} className="animate-spin" aria-hidden /> : <span className="tabular text-[13px] font-bold">{i + 1}</span>}
              </span>
              <span className="leading-5">
                <span className="block font-bold">{label}{key === "drawing" && <> <span className="tabular">{drawn}</span> {tr("sur", "of")} <span className="tabular">{total}</span></>}</span>
                <span className={cn("text-[13px] font-bold", done ? "text-succes" : "text-encre-douce")}>{state}</span>
              </span>
            </li>
          );
        })}
      </ol>

      {ep.status === "blocked" && (
        <Card className="mb-8 border-alerte"><p className="font-display text-[24px] leading-[30px] text-alerte">{tr("Épisode arrêté", "Episode stopped")}</p>
          {ep.error && <p className="mt-2">{ep.error}</p>}
          <p className="mt-2 font-bold">{tr("Les crédits non utilisés vous ont été rendus.", "Unused credits have been refunded.")}</p>
          {ep.series_id && (
            <p className="mt-4"><Link to="/series/$id" params={{ id: String(ep.series_id) }} className={btnClass("primary")}>{tr("Modifier mes personnages et relancer", "Edit my characters and start again")}</Link></p>
          )}
        </Card>
      )}
      {ep.status === "failed" && (
        <Card className="mb-8"><p className="font-bold text-alerte">{tr("L'épisode s'est interrompu.", "The episode was interrupted.")}</p>{ep.error && <p className="mt-2">{ep.error}</p>}
          <p className="mt-2 text-[14px] leading-5 text-encre-douce">
            {tr("Reprendre redessine seulement ce qui manque. Si l'interruption revient, abandonnez l'épisode : les crédits non utilisés vous sont rendus et vous pourrez en lancer un nouveau (après avoir modifié vos personnages si besoin).",
              "Resuming only redraws what's missing. If the interruption happens again, abandon the episode: unused credits are refunded and you can start a new one (after editing your characters if needed).")}
          </p>
          <ErrorNote error={resume.error ?? abandon.error} />
          <div className="mt-4 flex flex-wrap gap-3">
            <Button variant="primary" disabled={resume.isPending || abandon.isPending} onClick={() => resume.mutate()}><RotateCcw size={20} strokeWidth={2} aria-hidden />{tr("Reprendre", "Resume")}</Button>
            <Button disabled={resume.isPending || abandon.isPending} onClick={() => { if (confirm(tr("Abandonner cet épisode ? Les crédits non utilisés vous seront rendus.", "Abandon this episode? Unused credits will be refunded."))) abandon.mutate(); }}>{tr("Abandonner l'épisode", "Abandon the episode")}</Button>
          </div>
        </Card>
      )}
      {ep.status === "canceled" && (
        <Card className="mb-8"><p className="font-bold">{tr("Épisode abandonné.", "Episode abandoned.")}</p>
          <p className="mt-2 text-encre-douce">
            {tr("Les crédits non utilisés vous ont été rendus. Pour repartir de zéro, supprimez-le : ses pages et son scénario disparaissent, il n'influence plus la suite de l'histoire, et le prochain épisode reprendra son numéro.",
              "Unused credits have been refunded. To start from scratch, delete it: its pages and script disappear, it no longer affects the rest of the story, and the next episode takes its number.")}
          </p>
          <ErrorNote error={effacer.error} />
          <div className="mt-4 flex flex-wrap gap-3">
            <Button variant="primary" disabled={effacer.isPending}
              onClick={() => { if (confirm(tr("Supprimer définitivement cet épisode ? Ses pages et son scénario seront effacés. Cette action est irréversible.", "Delete this episode permanently? Its pages and script will be erased. This can't be undone."))) effacer.mutate(); }}>
              <Trash2 size={20} strokeWidth={2} aria-hidden />{effacer.isPending ? tr("Suppression…", "Deleting…") : tr("Supprimer définitivement", "Delete permanently")}
            </Button>
            {ep.series_id && <Link to="/series/$id" params={{ id: String(ep.series_id) }} className={btnClass()}>{tr("Retour à la série", "Back to the series")}</Link>}
          </div>
        </Card>
      )}

      <div className="grid gap-8 lg:grid-cols-[1fr_280px]">
        <section aria-label={tr("Page sélectionnée", "Selected page")}>
          <PageView url={page?.url} number={page?.number ?? 1} failed={page?.status === "failed"} stopped={!active} big />
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <Button aria-label={tr("Page précédente", "Previous page")} disabled={current <= 0} onClick={() => setCurrent((c) => c - 1)}><ChevronLeft size={20} strokeWidth={2} aria-hidden /></Button>
            <span className="tabular font-bold">Page {page?.number ?? 1} / {total}</span>
            <Button aria-label={tr("Page suivante", "Next page")} disabled={current >= pages.length - 1} onClick={() => setCurrent((c) => c + 1)}><ChevronRight size={20} strokeWidth={2} aria-hidden /></Button>
            <Button className="ml-auto" disabled={drawn === 0} onClick={() => setReader(true)}><Maximize2 size={20} strokeWidth={2} aria-hidden />{tr("Plein écran", "Full screen")}</Button>
          </div>
          {redrawing && <p role="status" className="mt-4 font-bold text-indigo">{tr("Redessin en cours…", "Redrawing…")}</p>}
          {me?.plan.redraw && page && (page.url || page.status === "failed") && !active && ep.status !== "blocked" && !redrawing && (
            <Redraw key={page.id} pageId={String(page.id)} onSent={() => setRedrawing({ pageId: String(page.id), attempts: page.attempts ?? 0, at: Date.now() })} />
          )}
        </section>
        <aside aria-label={tr("Toutes les pages", "All pages")}>
          <ul className="grid grid-cols-3 gap-3 lg:grid-cols-2">
            {pages.map((p, i) => (
              <li key={p.id}>
                <button onClick={() => setCurrent(i)} aria-current={i === current} aria-label={`Page ${p.number}${p.url ? "" : p.status === "failed" ? tr(", à refaire", ", to redo") : active ? tr(", en cours", ", in progress") : tr(", non dessinée", ", not drawn")}`} className={cn("block w-full", i === current && "outline-3 outline-offset-2 outline-vermillon")}>
                  <PageView url={p.url} number={p.number} failed={p.status === "failed"} stopped={!active} />
                </button>
              </li>
            ))}
          </ul>
        </aside>
      </div>

      {ep.usage && <UsageCard u={ep.usage} />}
      {finished && <PartagerChapitre ep={ep} />}
      {finished && <PublierChapitre episodeId={ep.id} />}
      {finished && <DonnerAvis episodeId={ep.id} compact />}
      {reader && <Reader pages={pages.filter((p) => p.url)} onClose={() => setReader(false)} />}
    </Container>
  );
}

function PageView({ url, number, big, failed, stopped }: { url?: string | null | undefined; number: number; big?: boolean; failed?: boolean; stopped?: boolean }) {
  const state = failed ? tr("À refaire", "To redo") : stopped ? tr("Non dessinée", "Not drawn") : tr("En cours", "In progress");
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
        <Field label={tr("Remarque pour cette page", "Note for this page")} htmlFor="note" hint={(m.error as { code?: string } | null)?.code === "blocked_terms" ? <ErrorNote inline error={m.error} /> : undefined}>
          <Textarea id="note" required minLength={3} maxLength={300} value={note} onChange={(e) => setNote(e.target.value)} placeholder={tr("Agrandir la case du milieu, regard plus déterminé…", "Make the middle panel bigger, a more determined look…")} />
        </Field>
        {(m.error as { code?: string } | null)?.code !== "blocked_terms" && <ErrorNote error={m.error} />}
        <Button type="submit" disabled={m.isPending}>{tr("Redessiner cette page · 1 crédit", "Redraw this page · 1 credit")}</Button>
      </form>
    </Card>
  );
}

function UsageCard({ u }: { u: NonNullable<Episode["usage"]> }) {
  return (
    <Card className="mt-12">
      <h2 className="font-display text-[24px] leading-[30px]">{tr("Consommation de l'épisode", "Episode usage")}</h2>
      <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[[tr("Tokens lus", "Tokens read"), u.input_tokens], [tr("Tokens écrits", "Tokens written"), u.output_tokens], [tr("Images", "Images"), u.images], [tr("Crédits", "Credits"), u.credits]].map(([l, v]) => (
          <div key={l as string} className="rounded-[4px] border-2 border-encre p-3"><dt className="label-caps">{l}</dt><dd className="tabular mt-1 text-right text-[20px] font-bold">{fmt(v as number)}</dd></div>
        ))}
      </dl>
      <div className="mt-6 overflow-x-auto">
        <table className="w-full min-w-[520px] text-[14px] leading-5">
          <thead><tr className="border-b-2 border-encre text-left"><th className="label-caps py-2">{tr("Étape", "Step")}</th><th className="label-caps py-2 text-right">{tr("Appels", "Calls")}</th><th className="label-caps py-2 text-right">{tr("Tokens lus", "Tokens read")}</th><th className="label-caps py-2 text-right">{tr("Tokens écrits", "Tokens written")}</th><th className="label-caps py-2 text-right">{tr("Images", "Images")}</th></tr></thead>
          <tbody>
            {[...u.stages].sort((a, b) => STAGE_ORDER.indexOf(a.stage) - STAGE_ORDER.indexOf(b.stage)).map((s) => (
              <tr key={s.stage} className="border-b border-trait">
                <td className="py-2 font-medium">{stageLabel(s.stage)}</td>
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
    <div className="dark fixed inset-0 z-50" role="dialog" aria-modal aria-label={tr("Lecteur plein écran", "Full-screen reader")}>
      <div className="flex h-full flex-col bg-papier text-encre">
        <div className="flex items-center justify-between gap-3 p-3">
          <span className="tabular font-bold">Page {p?.number} / {pages.length}</span>
          <Button aria-label={tr("Fermer le lecteur", "Close the reader")} onClick={onClose}><X size={20} strokeWidth={2} aria-hidden /></Button>
        </div>
        <div className="flex min-h-0 flex-1 items-center justify-center gap-3 px-3 pb-6">
          <Button aria-label={tr("Page précédente", "Previous page")} disabled={i === 0} onClick={() => setI(i - 1)}><ChevronLeft size={20} strokeWidth={2} aria-hidden /></Button>
          {p?.url && <img src={p.url} alt={`Page ${p.number}`} className="aspect-[2/3] h-full max-h-full min-w-0 border-2 border-encre bg-blanc object-contain" />}
          <Button aria-label={tr("Page suivante", "Next page")} disabled={i >= pages.length - 1} onClick={() => setI(i + 1)}><ChevronRight size={20} strokeWidth={2} aria-hidden /></Button>
        </div>
      </div>
    </div>
  );
}

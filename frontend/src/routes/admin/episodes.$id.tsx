import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ACTIVE, type Episode } from "@/lib/api";
import { CHECKPOINT_LABEL, dateTime, num, usd, type ModerationEvent } from "@/lib/admin";
import { Button, ErrorNote, Pill } from "@/components/ink";
import { EpisodeStatus, Section, Stat, Table } from "@/components/admin";

export const Route = createFileRoute("/admin/episodes/$id")({ component: EpisodeAdminPage });

type Detail = Episode & {
  summary?: string | null; series_title: string; premise: string; owner: { id: string; email: string } | null; created_at: string; direction: string;
  cost: { stage: string; model: string; calls: number; cost_usd: number }[]; cost_usd: number; moderation_events: ModerationEvent[];
};
const STAGE: Record<string, string> = {
  design: "Design des personnages", script: "Scénario", moderation: "Modération", sheet: "Fiches modèles",
  page: "Pages", check: "Relecture", cover: "Couverture", redraw: "Redessins demandés",
};

function EpisodeAdminPage() {
  const { id } = Route.useParams();
  const { data: e, error, isLoading } = useQuery({
    queryKey: ["admin", "episode", id], queryFn: () => api<Detail>(`/admin/episodes/${id}`),
    refetchInterval: (q) => (q.state.data && ACTIVE.includes(q.state.data.status) ? 3000 : false),
  });
  const qc = useQueryClient();
  const abandon = useMutation({
    mutationFn: () => api(`/admin/episodes/${id}/abandon`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin"] }),
  });
  const navigate = useNavigate();
  const effacer = useMutation({
    mutationFn: () => api(`/admin/episodes/${id}`, { method: "DELETE" }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["admin"] }); navigate({ to: "/admin/episodes" }); },
  });
  const effacerSerie = useMutation({
    mutationFn: (sid: string) => api(`/admin/series/${sid}`, { method: "DELETE" }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["admin"] }); navigate({ to: "/admin/episodes" }); },
  });
  if (isLoading) return <p className="text-encre-douce">Chargement de l'épisode…</p>;
  if (error || !e) return <ErrorNote error={error ?? new Error("Épisode introuvable.")} />;
  const u = e.usage;

  return (
    <>
      <Link to="/admin/episodes" className="inline-flex min-h-11 items-center font-bold text-indigo underline">Tous les épisodes</Link>
      <div className="mt-2 flex flex-wrap items-center gap-3">
        <h2 className="font-display text-[28px] leading-[34px]">{e.series_title || "Nouvelle série"} · n° {e.number}</h2>
        <EpisodeStatus status={e.status} />
      </div>
      <p className="mt-1 text-encre-douce">
        {e.title && <>{e.title} · </>}lancé le {dateTime(e.created_at)} par{" "}
        {e.owner ? <Link to="/admin/utilisateurs/$id" params={{ id: e.owner.id }} className="font-bold text-indigo underline">{e.owner.email}</Link> : "un compte supprimé"}
      </p>
      {e.error && <p role="alert" className="mt-4 rounded-[4px] border-2 border-alerte bg-bulle p-3 font-medium text-alerte">{e.error}</p>}
      {e.status === "canceled" && (
        <div className="mt-4 rounded-[4px] border-2 border-encre bg-bulle p-4">
          <p className="text-[14px] leading-5 text-encre-douce">
            Épisode abandonné. Le supprimer efface ses pages et son scénario ; ses coûts IA et les mouvements de crédits restent dans l'historique.
          </p>
          <Button className="mt-3" disabled={effacer.isPending} onClick={() => { if (confirm("Supprimer définitivement cet épisode ?")) effacer.mutate(); }}>
            Supprimer définitivement
          </Button>
          <ErrorNote error={effacer.error} />
        </div>
      )}
      {(e.status === "failed" || e.status === "blocked") && (
        <div className="mt-4 rounded-[4px] border-2 border-encre bg-bulle p-4">
          <p className="text-[14px] leading-5 text-encre-douce">
            L'auteur ne peut pas lancer d'autre épisode dans cette série tant que celui-ci est interrompu. L'abandonner le débloque :
            rien n'est plus dessiné, les crédits réservés et non utilisés lui sont rendus. L'action est notée dans le journal.
          </p>
          <Button className="mt-3" disabled={abandon.isPending} onClick={() => { if (confirm("Abandonner cet épisode et rendre les crédits non utilisés ?")) abandon.mutate(); }}>
            Abandonner l'épisode et rendre les crédits
          </Button>
          <ErrorNote error={abandon.error} />
        </div>
      )}

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Coût IA réel" value={usd(e.cost_usd, 3)} sub={u && u.credits ? <>{usd(e.cost_usd / u.credits, 3)} par crédit</> : undefined} />
        <Stat label="Crédits" value={num(u?.credits)} sub={<>{num(u?.images)} images dessinées</>} />
        <Stat label="Tokens" value={num((u?.input_tokens ?? 0) + (u?.output_tokens ?? 0))} sub={<>{num(u?.input_tokens)} lus · {num(u?.output_tokens)} écrits</>} />
        <Stat label="Pages" value={`${e.pages.filter((p) => p.url).length} / ${e.page_count}`} sub={<>{e.pages.filter((p) => (p.attempts ?? 0) > 1).length} redessinée(s)</>} />
      </div>

      <Section title="Pages">
        {e.pages.length === 0 ? <p className="text-encre-douce">Aucune page : le scénario n'a pas été validé.</p> : (
          <ul className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
            {e.pages.map((p) => (
              <li key={p.id}>
                {p.url ? (
                  <a href={p.url} target="_blank" rel="noreferrer" aria-label={`Ouvrir la page ${p.number}`}>
                    <img src={p.url} alt={`Page ${p.number}`} className="aspect-[2/3] w-full border-2 border-encre bg-blanc object-contain" />
                  </a>
                ) : <div className="trame aspect-[2/3] w-full border-2 border-encre" aria-hidden />}
                <p className="mt-1 text-[13px]"><span className="tabular font-bold">Page {p.number}</span>
                  {p.status === "failed" && <> · <span className="text-alerte">à refaire</span></>}
                  {(p.attempts ?? 0) > 1 && <> · {p.attempts} essais</>}</p>
                {p.editor_note && <p className="text-[12px] leading-4 text-encre-douce">{p.editor_note}</p>}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <div className="grid gap-x-8 lg:grid-cols-2">
        <Section title="Coût par étape">
          <Table head={["Étape", "Modèle", ["Appels", "right"], ["Coût", "right"]]} empty={e.cost.length === 0} minWidth={440}>
            {e.cost.map((c) => (
              <tr key={c.stage + c.model}>
                <td>{STAGE[c.stage] ?? c.stage}</td>
                <td className="tabular text-[13px]">{c.model}</td>
                <td className="tabular text-right">{num(c.calls)}</td>
                <td className="tabular text-right">{usd(c.cost_usd, 4)}</td>
              </tr>
            ))}
          </Table>
        </Section>
        <Section title="Modération">
          <Table head={["Quand", "Étape", "Règle"]} empty={e.moderation_events.length === 0} minWidth={420}>
            {e.moderation_events.map((m) => (
              <tr key={m.id}>
                <td className="tabular whitespace-nowrap">{dateTime(m.created_at)}</td>
                <td>{CHECKPOINT_LABEL[m.checkpoint] ?? m.checkpoint}</td>
                <td><Pill tone={m.action === "block" ? "alerte" : "soleil"}>{m.rule}</Pill>{m.excerpt && <p className="mt-1 text-[13px] text-encre-douce">{m.excerpt}</p>}</td>
              </tr>
            ))}
          </Table>
        </Section>
      </div>

      <Section title="Demande de l'auteur">
        <div className="rounded-[8px] border-2 border-encre bg-bulle p-4 shadow-ink">
          <p className="label-caps">Idée de la série</p><p className="mt-1">{e.premise}</p>
          <p className="label-caps mt-4">Pour cet épisode</p><p className="mt-1">{e.direction || "—"}</p>
          {e.summary && <><p className="label-caps mt-4">Résumé écrit</p><p className="mt-1">{e.summary}</p></>}
        </div>
      </Section>
      <section className="mt-12 border-t-2 border-encre pt-6">
        <h3 className="font-display text-[20px] leading-[26px]">Supprimer toute la série</h3>
        <p className="mt-1 max-w-3xl text-[14px] leading-5 text-encre-douce">
          À réserver aux signalements ou aux demandes de l'auteur : la série, ses personnages, tous ses épisodes et ses publications sont effacés.
          Les coûts IA et les mouvements de crédits restent dans l'historique. L'action est notée dans le journal.
        </p>
        <Button className="mt-3" disabled={effacerSerie.isPending || ACTIVE.includes(e.status)}
          onClick={() => { if (confirm(`Supprimer définitivement la série « ${e.series_title || "sans titre"} » et tous ses épisodes ?`)) effacerSerie.mutate(String(e.series_id)); }}>
          Supprimer la série
        </Button>
        <ErrorNote error={effacerSerie.error} />
      </section>
    </>
  );
}

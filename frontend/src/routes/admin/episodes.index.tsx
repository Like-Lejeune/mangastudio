import { createFileRoute, Link } from "@tanstack/react-router";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Search } from "lucide-react";
import { api } from "@/lib/api";
import { dateTime, num, usd, type AdminEpisode, type Paged } from "@/lib/admin";
import { Button, ErrorNote, Input } from "@/components/ink";
import { EpisodeStatus, Pager, selectCls, Table } from "@/components/admin";

export const Route = createFileRoute("/admin/episodes/")({ component: EpisodesPage });

function EpisodesPage() {
  const [draft, setDraft] = useState("");
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const { data, error, isFetching } = useQuery({
    queryKey: ["admin", "episodes", q, status, page],
    queryFn: () => api<Paged<AdminEpisode>>(`/admin/episodes?${new URLSearchParams({ q, status, page: String(page) })}`),
    placeholderData: keepPreviousData,
    refetchInterval: 15_000,
  });
  return (
    <>
      <form className="flex flex-wrap items-end gap-3" onSubmit={(e) => { e.preventDefault(); setQ(draft); setPage(1); }}>
        <div className="min-w-[240px] flex-1">
          <label htmlFor="q" className="label-caps mb-2 block">Rechercher</label>
          <Input id="q" value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Auteur, série ou titre" />
        </div>
        <div>
          <label htmlFor="status" className="label-caps mb-2 block">Statut</label>
          <select id="status" className={selectCls} value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
            <option value="">Tous</option>
            <option value="running">En cours</option>
            <option value="done">Terminés</option>
            <option value="failed">Interrompus</option>
            <option value="blocked">Refusés</option>
          </select>
        </div>
        <Button type="submit" variant="primary"><Search size={18} strokeWidth={2} aria-hidden />Rechercher</Button>
      </form>
      <div className="mt-6"><ErrorNote error={error} /></div>
      {data && (
        <div className={isFetching ? "opacity-80" : undefined}>
          <Table head={["Épisode", "Auteur", "Statut", ["Pages", "right"], ["Crédits", "right"], ["Images", "right"], ["Coût IA", "right"], "Lancé le"]} empty={data.items.length === 0} minWidth={900}>
            {data.items.map((e) => (
              <tr key={e.id}>
                <td>
                  <Link to="/admin/episodes/$id" params={{ id: e.id }} className="font-bold underline">{e.series_title || "Nouvelle série"} · n° {e.number}</Link>
                  {e.title && <p className="text-[13px] text-encre-douce">{e.title}</p>}
                  {e.error && <p className="mt-1 text-[13px] text-alerte">{e.error}</p>}
                </td>
                <td><Link to="/admin/utilisateurs/$id" params={{ id: e.owner_id }} className="break-all underline">{e.owner_email}</Link></td>
                <td><EpisodeStatus status={e.status} /></td>
                <td className="tabular text-right">{e.page_count}</td>
                <td className="tabular text-right">{num(e.credits)}</td>
                <td className="tabular text-right">{num(e.images)}</td>
                <td className="tabular text-right">{usd(e.cost_usd, 3)}</td>
                <td className="tabular whitespace-nowrap">{dateTime(e.created_at)}</td>
              </tr>
            ))}
          </Table>
          <Pager page={data.page} pages={data.pages} total={data.total} onPage={setPage} />
        </div>
      )}
    </>
  );
}

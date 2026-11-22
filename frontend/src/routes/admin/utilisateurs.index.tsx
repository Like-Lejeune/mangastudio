import { createFileRoute, Link } from "@tanstack/react-router";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Search } from "lucide-react";
import { api } from "@/lib/api";
import { day, num, type AdminUser, type Paged } from "@/lib/admin";
import { Button, ErrorNote, Input, Pill } from "@/components/ink";
import { Pager, selectCls, Table } from "@/components/admin";

export const Route = createFileRoute("/admin/utilisateurs/")({ component: UsersPage });

function UsersPage() {
  const [draft, setDraft] = useState("");
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("all");
  const [page, setPage] = useState(1);
  const { data, error, isFetching } = useQuery({
    queryKey: ["admin", "users", q, status, page],
    queryFn: () => api<Paged<AdminUser>>(`/admin/users?${new URLSearchParams({ q, status, page: String(page) })}`),
    placeholderData: keepPreviousData,
  });

  return (
    <>
      <form className="flex flex-wrap items-end gap-3" onSubmit={(e) => { e.preventDefault(); setQ(draft); setPage(1); }}>
        <div className="min-w-[240px] flex-1">
          <label htmlFor="q" className="label-caps mb-2 block">Rechercher</label>
          <Input id="q" value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Adresse e-mail ou nom" />
        </div>
        <div>
          <label htmlFor="status" className="label-caps mb-2 block">Afficher</label>
          <select id="status" className={selectCls} value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
            <option value="all">Tous les comptes</option>
            <option value="active">Actifs</option>
            <option value="suspended">Suspendus</option>
            <option value="admin">Administrateurs</option>
            <option value="unverified">E-mail non confirmé</option>
          </select>
        </div>
        <Button type="submit" variant="primary"><Search size={18} strokeWidth={2} aria-hidden />Rechercher</Button>
      </form>
      <div className="mt-6"><ErrorNote error={error} /></div>
      {data && (
        <div className={isFetching ? "opacity-60" : undefined}>
          <Table head={["Utilisateur", "Plan", ["Crédits", "right"], ["Épisodes", "right"], "Dernier épisode", "Inscrit le", "État"]} empty={data.items.length === 0}>
            {data.items.map((u) => (
              <tr key={u.id}>
                <td>
                  <Link to="/admin/utilisateurs/$id" params={{ id: u.id }} className="font-bold underline">{u.display_name}</Link>
                  <p className="break-all text-[13px] text-encre-douce">{u.email}</p>
                </td>
                <td>{u.plan_name}</td>
                <td className="tabular text-right">{num(u.credits)}</td>
                <td className="tabular text-right">{num(u.episodes)}</td>
                <td className="tabular whitespace-nowrap">{day(u.last_episode_at)}</td>
                <td className="tabular whitespace-nowrap">{day(u.created_at)}</td>
                <td className="space-x-1 whitespace-nowrap">
                  {u.is_active ? <Pill tone="succes">Actif</Pill> : <Pill tone="alerte">Suspendu</Pill>}
                  {!u.email_verified && <Pill tone="soleil">Non confirmé</Pill>}
                  {u.is_admin && <Pill tone="indigo">Admin</Pill>}
                </td>
              </tr>
            ))}
          </Table>
          <Pager page={data.page} pages={data.pages} total={data.total} onPage={setPage} />
        </div>
      )}
    </>
  );
}

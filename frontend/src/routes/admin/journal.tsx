import { createFileRoute, Link } from "@tanstack/react-router";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { ACTION_LABEL, dateTime, type AdminAction, type Paged } from "@/lib/admin";
import { ErrorNote } from "@/components/ink";
import { Pager, Table } from "@/components/admin";

export const Route = createFileRoute("/admin/journal")({ component: JournalPage });

function JournalPage() {
  const [page, setPage] = useState(1);
  const { data, error } = useQuery({
    queryKey: ["admin", "actions", page], queryFn: () => api<Paged<AdminAction>>(`/admin/actions?page=${page}`), placeholderData: keepPreviousData,
  });
  return (
    <>
      <p className="mb-4 max-w-3xl text-[14px] leading-5 text-encre-douce">
        Toutes les actions des administrateurs (crédits, plans, suspensions, droits, règles de modération) et les alertes de budget IA envoyées par la plateforme. Ce journal ne peut être ni modifié ni effacé depuis la plateforme.
      </p>
      <ErrorNote error={error} />
      {data && <>
        <Table head={["Quand", "Administrateur", "Action", "Sur", "Détail"]} empty={data.items.length === 0}>
          {data.items.map((a) => (
            <tr key={a.id}>
              <td className="tabular whitespace-nowrap">{dateTime(a.created_at)}</td>
              <td className="break-all">{a.admin_email}</td>
              <td className="font-bold">{ACTION_LABEL[a.action] ?? a.action}</td>
              <td>{a.target_type === "platform" ? "Plateforme" : a.target_type === "user" ? <Link to="/admin/utilisateurs/$id" params={{ id: a.target_id }} className="underline">Voir le compte</Link> : a.target_id}</td>
              <td>{a.detail}</td>
            </tr>
          ))}
        </Table>
        <Pager page={data.page} pages={data.pages} total={data.total} onPage={setPage} />
      </>}
    </>
  );
}

import { createFileRoute, Link } from "@tanstack/react-router";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Star } from "lucide-react";
import { api } from "@/lib/api";
import { dateTime, type Paged } from "@/lib/admin";
import { Button, ErrorNote, Pill } from "@/components/ink";
import { Pager } from "@/components/admin";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/admin/avis")({ component: AvisPage });

type AvisAdmin = {
  id: string; text: string; rating: number; display_name: string; role: string; status: "pending" | "approved" | "rejected";
  user_id: string; user_email: string | null; created_at: string; reviewed_at: string | null;
};
const ONGLETS = [["pending", "À relire"], ["approved", "Publiés"], ["rejected", "Refusés"]] as const;

function AvisPage() {
  const qc = useQueryClient();
  const [statut, setStatut] = useState<(typeof ONGLETS)[number][0]>("pending");
  const [page, setPage] = useState(1);
  const { data, error } = useQuery({
    queryKey: ["admin", "avis", statut, page],
    queryFn: () => api<Paged<AvisAdmin>>(`/admin/testimonials?status=${statut}&page=${page}`),
    placeholderData: keepPreviousData,
  });
  const decider = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => api(`/admin/testimonials/${id}/status`, { body: { status } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin"] }),
  });

  return (
    <>
      <p className="mb-4 max-w-3xl text-[14px] leading-5 text-encre-douce">
        Chaque avis a été envoyé avec l'accord de publication de son auteur. Seuls les avis publiés apparaissent sur la page d'accueil (12 au plus, les plus récents). Un avis modifié par son auteur revient ici, à relire.
      </p>
      <div className="mb-6 flex flex-wrap gap-2" role="tablist">
        {ONGLETS.map(([v, l]) => (
          <button key={v} role="tab" aria-selected={statut === v} onClick={() => { setStatut(v); setPage(1); }}
            className={cn("min-h-11 rounded-[4px] border-2 border-encre px-4 font-bold", statut === v ? "bg-encre text-bulle" : "bg-bulle hover:bg-soleil")}>
            {l}
          </button>
        ))}
      </div>
      <ErrorNote error={error ?? decider.error} />
      {data && data.items.length === 0 && <p className="text-encre-douce">Aucun avis ici pour l'instant.</p>}
      <ul className="grid gap-4 lg:grid-cols-2">
        {data?.items.map((a) => (
          <li key={a.id} className="flex flex-col rounded-[8px] border-2 border-encre bg-bulle p-5 shadow-ink">
            <p className="flex gap-0.5" aria-label={`${a.rating} sur 5`}>
              {[1, 2, 3, 4, 5].map((n) => <Star key={n} size={18} strokeWidth={2} aria-hidden className={n <= a.rating ? "fill-soleil text-encre" : "text-trait"} />)}
            </p>
            <p className="mt-3 flex-1 text-[17px] leading-7">« {a.text} »</p>
            <p className="mt-3"><b>{a.display_name}</b>{a.role && <span className="text-encre-douce"> · {a.role}</span>}</p>
            <p className="mt-1 text-[13px] text-encre-douce">
              Envoyé le {dateTime(a.created_at)} par{" "}
              <Link to="/admin/utilisateurs/$id" params={{ id: a.user_id }} className="underline">{a.user_email ?? "compte supprimé"}</Link>
              {a.reviewed_at && <> · décidé le {dateTime(a.reviewed_at)}</>}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {a.status !== "approved" && <Button variant="primary" disabled={decider.isPending} onClick={() => decider.mutate({ id: a.id, status: "approved" })}>Publier</Button>}
              {a.status !== "rejected" && <Button disabled={decider.isPending} onClick={() => decider.mutate({ id: a.id, status: "rejected" })}>{a.status === "approved" ? "Retirer de l'accueil" : "Refuser"}</Button>}
              {a.status === "rejected" && <Pill>Non publié</Pill>}
            </div>
          </li>
        ))}
      </ul>
      {data && data.pages > 1 && <Pager page={data.page} pages={data.pages} total={data.total} onPage={setPage} />}
    </>
  );
}

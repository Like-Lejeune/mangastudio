import { createFileRoute, Link } from "@tanstack/react-router";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { dateTime, type Paged } from "@/lib/admin";
import { Button, ErrorNote, Pill } from "@/components/ink";
import { Pager, selectCls, Table } from "@/components/admin";

export const Route = createFileRoute("/admin/parrainages")({ component: ParrainagesPage });

type Ligne = {
  id: string; status: "pending" | "qualified" | "flagged" | "cancelled"; flag_reason: string; created_at: string;
  referrer_id: string; referrer_email: string; referee_id: string; referee_email: string; referee_verified: boolean; referee_ip: string | null;
  invitee_rewarded: boolean; referrer_rewarded: boolean; purchase_rewarded: boolean;
};
const ETAT = { pending: ["En attente", "bulle"], qualified: ["Récompensé", "succes"], flagged: ["À vérifier", "soleil"], cancelled: ["Annulé", "alerte"] } as const;

function ParrainagesPage() {
  const qc = useQueryClient();
  const [statut, setStatut] = useState("flagged");
  const [page, setPage] = useState(1);
  const { data, error } = useQuery({
    queryKey: ["admin", "parrainages", statut, page],
    queryFn: () => api<Paged<Ligne> & { flagged: number }>(`/admin/referrals?status=${statut}&page=${page}`),
    placeholderData: keepPreviousData,
  });
  const decider = useMutation({
    mutationFn: ({ id, action }: { id: string; action: "approve" | "cancel" }) => api(`/admin/referrals/${id}/${action}`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin"] }),
  });

  return (
    <>
      <p className="mb-4 max-w-3xl text-[14px] leading-5 text-encre-douce">
        Un parrainage est mis de côté quand le filleul s'inscrit depuis la même connexion que son parrain, ou quand plusieurs filleuls arrivent de la même connexion en 24 h.
        Attention : beaucoup d'abonnés mobiles partagent la même adresse IP, donc une famille ou des voisins peuvent être signalés à tort.
        « Valider » verse les récompenses dues ; « Annuler » bloque les suivantes (retirez à la main, depuis la fiche du parrain, ce qui a déjà été versé).
      </p>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <label htmlFor="st" className="label-caps">Afficher</label>
        <select id="st" className={selectCls} value={statut} onChange={(e) => { setStatut(e.target.value); setPage(1); }}>
          <option value="flagged">À vérifier ({data?.flagged ?? "…"})</option>
          <option value="">Tous</option>
          <option value="pending">En attente du 1er épisode</option>
          <option value="qualified">Récompensés</option>
          <option value="cancelled">Annulés</option>
        </select>
      </div>
      <ErrorNote error={error ?? decider.error} />
      {data && <>
        <Table head={["Quand", "Parrain", "Filleul", "État", "Versé", ""]} empty={data.items.length === 0} minWidth={980}>
          {data.items.map((r) => (
            <tr key={r.id}>
              <td className="tabular whitespace-nowrap">{dateTime(r.created_at)}</td>
              <td><Link to="/admin/utilisateurs/$id" params={{ id: r.referrer_id }} className="break-all underline">{r.referrer_email}</Link></td>
              <td>
                <Link to="/admin/utilisateurs/$id" params={{ id: r.referee_id }} className="break-all underline">{r.referee_email}</Link>
                <p className="text-[12px] text-encre-douce">{r.referee_verified ? "adresse confirmée" : "adresse non confirmée"}{r.referee_ip && <> · IP {r.referee_ip}</>}</p>
              </td>
              <td><Pill tone={ETAT[r.status][1]}>{ETAT[r.status][0]}</Pill>{r.flag_reason && <p className="mt-1 text-[12px] text-alerte">{r.flag_reason}</p>}</td>
              <td className="text-[13px]">
                {[r.invitee_rewarded && "filleul +5", r.referrer_rewarded && "parrain +10", r.purchase_rewarded && "achat +25"].filter(Boolean).join(" · ") || "—"}
              </td>
              <td className="whitespace-nowrap">
                {r.status === "flagged" && <Button variant="primary" className="mr-2 min-h-10 px-3 text-[14px]" disabled={decider.isPending} onClick={() => decider.mutate({ id: r.id, action: "approve" })}>Valider</Button>}
                {r.status !== "cancelled" && <Button className="min-h-10 px-3 text-[14px]" disabled={decider.isPending} onClick={() => decider.mutate({ id: r.id, action: "cancel" })}>Annuler</Button>}
              </td>
            </tr>
          ))}
        </Table>
        <Pager page={data.page} pages={data.pages} total={data.total} onPage={setPage} />
      </>}
    </>
  );
}

import { createFileRoute, Link } from "@tanstack/react-router";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Heart, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { dateTime, type Paged } from "@/lib/admin";
import { titreHistoire, type CarteHistoire } from "@/lib/galerie";
import { Button, ErrorNote, Input, Pill } from "@/components/ink";
import { Pager } from "@/components/admin";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/admin/publications")({ component: PublicationsPage });

type PubAdmin = CarteHistoire & {
  status: "pending" | "published" | "rejected" | "withdrawn"; reason: string; episode_id: string; user_id: string; email: string;
  requested_at: string | null; page_urls: string[];
};
const ONGLETS = [["pending", "À relire"], ["published", "Publiées"], ["featured", "Coups de cœur"], ["rejected", "Refusées"], ["withdrawn", "Retirées"]] as const;
type Action = "approve" | "reject" | "withdraw" | "feature" | "unfeature";

function PublicationsPage() {
  const qc = useQueryClient();
  const [statut, setStatut] = useState<(typeof ONGLETS)[number][0]>("pending");
  const [page, setPage] = useState(1);
  const { data, error } = useQuery({
    queryKey: ["admin", "publications", statut, page],
    queryFn: () => api<Paged<PubAdmin> & { pending: number }>(`/admin/publications?status=${statut}&page=${page}`),
    placeholderData: keepPreviousData,
  });
  const decider = useMutation({
    mutationFn: ({ id, action, reason = "" }: { id: string; action: Action; reason?: string }) => api(`/admin/publications/${id}`, { body: { action, reason } }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["admin"] }); qc.invalidateQueries({ queryKey: ["galerie"] }); },
  });

  return (
    <>
      <p className="mb-4 max-w-3xl text-[14px] leading-5 text-encre-douce">
        Les auteurs ont accepté les <Link to="/regles-publication" className="underline">règles de publication</Link>. Lisez le chapitre en entier avant de le publier.
        Un refus ou un retrait exige un motif : il est montré à l'auteur, qui peut corriger et proposer à nouveau. Chaque décision est notée dans le journal.
      </p>
      <div className="mb-6 flex flex-wrap gap-2" role="tablist">
        {ONGLETS.map(([v, l]) => (
          <button key={v} role="tab" aria-selected={statut === v} onClick={() => { setStatut(v); setPage(1); }}
            className={cn("min-h-11 rounded-[4px] border-2 border-encre px-4 font-bold", statut === v ? "bg-encre text-bulle" : "bg-bulle hover:bg-soleil")}>
            {l}{v === "pending" && (data?.pending ?? 0) > 0 && <span className="tabular ml-2 rounded-full bg-vermillon px-2 text-[12px] text-sur-vermillon">{data?.pending}</span>}
          </button>
        ))}
      </div>
      <ErrorNote error={error ?? decider.error} />
      {data && data.items.length === 0 && <p className="text-encre-douce">Rien ici pour l'instant.</p>}
      <ul className="grid gap-5">
        {data?.items.map((p) => <Ligne key={p.id} p={p} busy={decider.isPending} onDecide={(action, reason) => decider.mutate({ id: p.id, action, reason })} />)}
      </ul>
      {data && data.pages > 1 && <Pager page={data.page} pages={data.pages} total={data.total} onPage={setPage} />}
    </>
  );
}

function Ligne({ p, busy, onDecide }: { p: PubAdmin; busy: boolean; onDecide: (a: Action, reason?: string) => void }) {
  const [motif, setMotif] = useState("");
  const [ouvert, setOuvert] = useState<"reject" | "withdraw" | null>(null);
  return (
    <li className="rounded-[8px] border-2 border-encre bg-bulle p-5 shadow-ink">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-display text-[20px] leading-[26px]">{titreHistoire(p)}</h3>
          <p className="mt-1 text-[13px] text-encre-douce">
            par <b className="text-encre">{p.author}</b> (<Link to="/admin/utilisateurs/$id" params={{ id: p.user_id }} className="underline">{p.email}</Link>)
            {" "}· demandé le {p.requested_at ? dateTime(p.requested_at) : "—"} · {p.pages} pages
          </p>
        </div>
        <div className="flex items-center gap-2">
          {p.featured && <Pill tone="soleil"><Sparkles size={14} strokeWidth={2.5} aria-hidden /> Coup de cœur</Pill>}
          <Pill><Heart size={14} strokeWidth={2.5} aria-hidden /> <span className="tabular">{p.likes}</span></Pill>
        </div>
      </div>
      {p.reason && <p className="mt-2 text-[14px]"><b>Motif : </b>{p.reason}</p>}
      <div className="mt-4 flex gap-2 overflow-x-auto">
        {p.page_urls.map((u, i) => <img key={u} src={u} alt={`Page ${i + 1}`} loading="lazy" className="h-40 w-auto rounded-[4px] border-2 border-encre" />)}
      </div>
      <p className="mt-2 text-[14px]">
        <Link to="/admin/episodes/$id" params={{ id: p.episode_id }} className="font-bold text-indigo underline">Lire le chapitre en entier</Link>
        {p.status === "published" && <> · <Link to="/galerie/$id" params={{ id: p.id }} className="font-bold text-indigo underline">Voir dans la galerie</Link></>}
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {p.status !== "published" && <Button variant="primary" disabled={busy} onClick={() => onDecide("approve")}>Publier</Button>}
        {p.status === "pending" && <Button disabled={busy} onClick={() => setOuvert("reject")}>Refuser…</Button>}
        {p.status === "published" && (
          <>
            <Button disabled={busy} onClick={() => onDecide(p.featured ? "unfeature" : "feature")}>{p.featured ? "Retirer des coups de cœur" : "Coup de cœur"}</Button>
            <Button disabled={busy} onClick={() => setOuvert("withdraw")}>Retirer…</Button>
          </>
        )}
      </div>
      {ouvert && (
        <form className="mt-3 flex flex-wrap items-end gap-2" onSubmit={(e) => { e.preventDefault(); onDecide(ouvert, motif); setOuvert(null); setMotif(""); }}>
          <label className="min-w-0 flex-1">
            <span className="mb-1 block text-[14px] font-bold">Motif montré à l'auteur</span>
            <Input value={motif} onChange={(e) => setMotif(e.target.value)} maxLength={300} required minLength={3} placeholder="Ex. : personnage d'un manga existant (règle 1)" />
          </label>
          <Button variant="primary" type="submit" disabled={busy || motif.trim().length < 3}>{ouvert === "reject" ? "Refuser" : "Retirer"}</Button>
          <Button type="button" onClick={() => setOuvert(null)}>Annuler</Button>
        </form>
      )}
    </li>
  );
}

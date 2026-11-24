import { Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { BookOpen, Heart } from "lucide-react";
import { api } from "@/lib/api";
import type { MaPublication } from "@/lib/galerie";
import { Button, Card, ErrorNote, Pill } from "@/components/ink";

const ETAT: Record<string, [string, "soleil" | "succes" | "alerte" | "bulle"]> = {
  pending: ["En cours de relecture", "soleil"],
  published: ["Publié dans la galerie", "succes"],
  rejected: ["Refusé", "alerte"],
  withdrawn: ["Retiré", "bulle"],
};

/** Sous un épisode terminé : le proposer à la galerie « À lire », suivre la relecture, le retirer. */
export function PublierChapitre({ episodeId }: { episodeId: string }) {
  const qc = useQueryClient();
  const [accepte, setAccepte] = useState(false);
  const key = ["publication", episodeId];
  const { data: pub, isLoading } = useQuery({ queryKey: key, queryFn: () => api<MaPublication>(`/episodes/${episodeId}/publication`) });
  const demander = useMutation({
    mutationFn: () => api<MaPublication>(`/episodes/${episodeId}/publication`, { body: { accept_terms: accepte } }),
    onSuccess: (d) => { qc.setQueryData(key, d); qc.invalidateQueries({ queryKey: ["galerie"] }); },
  });
  const retirer = useMutation({
    mutationFn: () => api<MaPublication>(`/episodes/${episodeId}/publication`, { method: "DELETE" }),
    onSuccess: (d) => { qc.setQueryData(key, d); qc.invalidateQueries({ queryKey: ["galerie"] }); },
  });
  if (isLoading) return null;
  const enLigne = pub?.status === "pending" || pub?.status === "published";

  return (
    <Card className="mt-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 font-display text-[22px] leading-[28px]"><BookOpen size={22} strokeWidth={2} aria-hidden />Publier dans la galerie « À lire »</h2>
        {pub && <Pill tone={ETAT[pub.status]?.[1]}>{ETAT[pub.status]?.[0]}</Pill>}
      </div>

      {pub?.status === "published" && (
        <p className="mt-2 text-encre-douce">
          Tout le monde peut le lire dans la galerie.{" "}
          <b className="inline-flex items-center gap-1 text-encre"><Heart size={16} strokeWidth={2.5} aria-hidden /><span className="tabular">{pub.likes}</span> j'aime</b>
          {pub.featured && <> · <b className="text-encre">Coup de cœur de l'équipe !</b></>}{" "}
          <Link to="/galerie/$id" params={{ id: pub.id }} className="font-bold text-indigo underline">Voir dans la galerie</Link>
        </p>
      )}
      {pub?.status === "pending" && <p className="mt-2 text-encre-douce">L'équipe relit votre chapitre. Il apparaîtra dans la galerie dès qu'il sera validé.</p>}
      {(pub?.status === "rejected" || pub?.status === "withdrawn") && pub.reason && (
        <p className="mt-2 rounded-[4px] border-2 border-encre bg-papier p-3"><b>Motif : </b>{pub.reason}</p>
      )}

      {!enLigne && (
        <>
          <p className="mt-2 text-encre-douce">
            {pub ? "Vous pouvez le proposer à nouveau." : "Faites lire votre chapitre à toute la communauté : il sera relu par l'équipe, puis les lecteurs pourront l'aimer. Les plus aimés passent sur la page d'accueil."}
          </p>
          <label className="mt-4 flex cursor-pointer items-start gap-3">
            <input type="checkbox" className="mt-1 size-5 accent-[var(--encre)]" checked={accepte} onChange={(e) => setAccepte(e.target.checked)} />
            <span>J'ai lu et j'accepte les <Link to="/regles-publication" target="_blank" className="font-bold text-indigo underline">règles de publication</Link> : cette histoire est la mienne et respecte ces règles.</span>
          </label>
          <Button variant="primary" className="mt-4" disabled={!accepte || demander.isPending} onClick={() => demander.mutate()}>
            {demander.isPending ? "Envoi…" : "Proposer ce chapitre"}
          </Button>
        </>
      )}
      {enLigne && (
        <button className="mt-4 inline-flex min-h-11 items-center text-[14px] font-bold text-alerte underline" disabled={retirer.isPending}
          onClick={() => { if (confirm("Retirer ce chapitre de la galerie ? Vous pourrez le proposer à nouveau.")) retirer.mutate(); }}>
          {pub?.status === "pending" ? "Annuler ma demande" : "Retirer de la galerie"}
        </button>
      )}
      <div className="mt-3"><ErrorNote error={demander.error ?? retirer.error} /></div>
    </Card>
  );
}

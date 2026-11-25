import { Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { BookOpen, Heart } from "lucide-react";
import { api } from "@/lib/api";
import type { MaPublication } from "@/lib/galerie";
import { Button, Card, ErrorNote, Pill } from "@/components/ink";
import { tr } from "@/lib/i18n";

const etat = (s: string): [string, "soleil" | "succes" | "alerte" | "bulle"] | undefined => ({
  pending: [tr("En cours de relecture", "Under review"), "soleil"],
  published: [tr("Publié dans la galerie", "Published in the gallery"), "succes"],
  rejected: [tr("Refusé", "Refused"), "alerte"],
  withdrawn: [tr("Retiré", "Withdrawn"), "bulle"],
} as Record<string, [string, "soleil" | "succes" | "alerte" | "bulle"]>)[s];

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
        <h2 className="flex items-center gap-2 font-display text-[22px] leading-[28px]"><BookOpen size={22} strokeWidth={2} aria-hidden />{tr("Publier dans la galerie « À lire »", "Publish in the “Read” gallery")}</h2>
        {pub && <Pill tone={etat(pub.status)?.[1]}>{etat(pub.status)?.[0]}</Pill>}
      </div>

      {pub?.status === "published" && (
        <p className="mt-2 text-encre-douce">
          {tr("Tout le monde peut le lire dans la galerie.", "Everyone can read it in the gallery.")}{" "}
          <b className="inline-flex items-center gap-1 text-encre"><Heart size={16} strokeWidth={2.5} aria-hidden /><span className="tabular">{pub.likes}</span> {tr("j'aime", "likes")}</b>
          {pub.featured && <> · <b className="text-encre">{tr("Coup de cœur de l'équipe !", "Staff pick!")}</b></>}{" "}
          <Link to="/galerie/$id" params={{ id: pub.id }} className="font-bold text-indigo underline">{tr("Voir dans la galerie", "See in the gallery")}</Link>
        </p>
      )}
      {pub?.status === "pending" && <p className="mt-2 text-encre-douce">{tr("L'équipe relit votre chapitre. Il apparaîtra dans la galerie dès qu'il sera validé.", "The team is reviewing your chapter. It will appear in the gallery as soon as it is approved.")}</p>}
      {(pub?.status === "rejected" || pub?.status === "withdrawn") && pub.reason && (
        <p className="mt-2 rounded-[4px] border-2 border-encre bg-papier p-3"><b>{tr("Motif : ", "Reason: ")}</b>{pub.reason}</p>
      )}

      {!enLigne && (
        <>
          <p className="mt-2 text-encre-douce">
            {pub ? tr("Vous pouvez le proposer à nouveau.", "You can submit it again.") : tr("Faites lire votre chapitre à toute la communauté : il sera relu par l'équipe, puis les lecteurs pourront l'aimer. Les plus aimés passent sur la page d'accueil.", "Let the whole community read your chapter: the team reviews it, then readers can like it. The most liked ones go on the home page.")}
          </p>
          <label className="mt-4 flex cursor-pointer items-start gap-3">
            <input type="checkbox" className="mt-1 size-5 accent-[var(--encre)]" checked={accepte} onChange={(e) => setAccepte(e.target.checked)} />
            <span>{tr("J'ai lu et j'accepte les ", "I have read and accept the ")}<Link to="/regles-publication" target="_blank" className="font-bold text-indigo underline">{tr("règles de publication", "publishing rules")}</Link>{tr(" : cette histoire est la mienne et respecte ces règles.", ": this story is mine and follows these rules.")}</span>
          </label>
          <Button variant="primary" className="mt-4" disabled={!accepte || demander.isPending} onClick={() => demander.mutate()}>
            {demander.isPending ? tr("Envoi…", "Sending…") : tr("Proposer ce chapitre", "Submit this chapter")}
          </Button>
        </>
      )}
      {enLigne && (
        <button className="mt-4 inline-flex min-h-11 items-center text-[14px] font-bold text-alerte underline" disabled={retirer.isPending}
          onClick={() => { if (confirm(tr("Retirer ce chapitre de la galerie ? Vous pourrez le proposer à nouveau.", "Remove this chapter from the gallery? You can submit it again later."))) retirer.mutate(); }}>
          {pub?.status === "pending" ? tr("Annuler ma demande", "Cancel my request") : tr("Retirer de la galerie", "Remove from the gallery")}
        </button>
      )}
      <div className="mt-3"><ErrorNote error={demander.error ?? retirer.error} /></div>
    </Card>
  );
}

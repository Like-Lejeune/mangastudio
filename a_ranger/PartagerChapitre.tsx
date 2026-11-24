import { Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Check, Copy, Download, Link2, Link2Off, Share2 } from "lucide-react";
import { api, downloadFile, type Episode } from "@/lib/api";
import { Button, Card, ErrorNote } from "@/components/ink";

type Quota = { limit: number | null; used: number; watermark: boolean };

/** Sous un épisode terminé : lien de partage public et téléchargement PDF. */
export function PartagerChapitre({ ep }: { ep: Episode }) {
  const qc = useQueryClient();
  const [copie, setCopie] = useState(false);
  const { data: quota } = useQuery({ queryKey: ["pdf-quota"], queryFn: () => api<Quota>("/me/pdf-quota") });

  const partager = useMutation({
    mutationFn: (enabled: boolean) => api<{ url: string | null }>(`/episodes/${ep.id}/share`, { body: { enabled } }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["episode", ep.id] }),
  });
  const pdf = useMutation({
    mutationFn: () => downloadFile(`/episodes/${ep.id}/pdf`, `episode-${ep.number}.pdf`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pdf-quota"] }),
  });

  const url = ep.share_url ?? null;
  const message = `Lisez mon manga « ${ep.title || `Épisode ${ep.number}`} », créé avec MangaStudio : ${url}`;
  const copier = async () => {
    if (!url) return;
    try { await navigator.clipboard.writeText(url); setCopie(true); setTimeout(() => setCopie(false), 2500); } catch { /* presse-papiers refusé */ }
  };
  const natif = typeof navigator !== "undefined" && "share" in navigator;
  const restant = quota?.limit != null ? Math.max(0, quota.limit - quota.used) : null;

  return (
    <div className="mt-8 grid gap-6 lg:grid-cols-2">
      <Card>
        <h2 className="flex items-center gap-2 font-display text-[22px] leading-[28px]"><Share2 size={22} strokeWidth={2} aria-hidden />Partager ce chapitre</h2>
        {!url ? (
          <>
            <p className="mt-2 text-encre-douce">Le chapitre est privé. Créez un lien : toute personne qui l'a pourra le lire, sans compte. Vous pourrez le couper à tout moment.</p>
            <Button variant="primary" className="mt-4" disabled={partager.isPending} onClick={() => partager.mutate(true)}>
              <Link2 size={18} strokeWidth={2} aria-hidden />Créer le lien de partage
            </Button>
          </>
        ) : (
          <>
            <p className="mt-2 text-encre-douce">Toute personne qui a ce lien peut lire le chapitre.</p>
            <div className="mt-3 flex items-stretch gap-2">
              <input readOnly value={url} aria-label="Lien de partage" onFocus={(e) => e.currentTarget.select()}
                className="tabular min-w-0 flex-1 rounded-[4px] border-2 border-encre bg-blanc px-3 text-[14px]" />
              <Button onClick={copier} aria-label="Copier le lien">{copie ? <Check size={18} strokeWidth={2} aria-hidden /> : <Copy size={18} strokeWidth={2} aria-hidden />}{copie ? "Copié" : "Copier"}</Button>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <a href={`https://wa.me/?text=${encodeURIComponent(message)}`} target="_blank" rel="noreferrer"
                className="inline-flex min-h-11 items-center rounded-[4px] border-2 border-encre bg-[#25D366] px-4 font-bold text-encre">WhatsApp</a>
              <a href={`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`} target="_blank" rel="noreferrer"
                className="inline-flex min-h-11 items-center rounded-[4px] border-2 border-encre bg-[#1877F2] px-4 font-bold text-white">Facebook</a>
              {natif && <Button onClick={() => navigator.share({ title: ep.title || `Épisode ${ep.number}`, text: message, url }).catch(() => {})}>Autres…</Button>}
            </div>
            <button className="mt-4 inline-flex min-h-11 items-center gap-2 text-[14px] font-bold text-alerte underline" disabled={partager.isPending} onClick={() => partager.mutate(false)}>
              <Link2Off size={16} strokeWidth={2} aria-hidden />Couper le lien (il ne marchera plus)
            </button>
          </>
        )}
        <ErrorNote error={partager.error} />
      </Card>

      <Card>
        <h2 className="flex items-center gap-2 font-display text-[22px] leading-[28px]"><Download size={22} strokeWidth={2} aria-hidden />Télécharger en PDF</h2>
        {quota?.watermark === false ? (
          <p className="mt-2 text-encre-douce">Inclus dans votre plan : PDF illimités, sans filigrane.</p>
        ) : (
          <p className="mt-2 text-encre-douce">
            Plan gratuit : PDF avec le filigrane MangaStudio, {quota?.limit ?? 3} chapitres par mois.{" "}
            {restant !== null && <b className="text-encre">Encore {restant} ce mois-ci.</b>}{" "}
            <Link to="/abonnements" className="font-bold text-indigo underline">Sans filigrane et illimité avec un plan payant</Link>.
          </p>
        )}
        <Button variant="primary" className="mt-4" disabled={pdf.isPending} onClick={() => pdf.mutate()}>
          <Download size={18} strokeWidth={2} aria-hidden />{pdf.isPending ? "Préparation du PDF…" : "Télécharger le PDF"}
        </Button>
        {pdf.isSuccess && <p role="status" className="mt-3 font-bold text-succes">PDF téléchargé.</p>}
        <div className="mt-3"><ErrorNote error={pdf.error} /></div>
      </Card>
    </div>
  );
}

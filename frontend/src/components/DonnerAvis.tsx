import { Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Star } from "lucide-react";
import { api } from "@/lib/api";
import { Button, Card, ErrorNote, Field, Input, Pill, Textarea } from "@/components/ink";
import { cn } from "@/lib/utils";
import { tr } from "@/lib/i18n";

export type MonAvis = {
  id: string; text: string; rating: number; display_name: string; role: string;
  status: "pending" | "approved" | "rejected"; created_at: string;
} | null;

const etat = (s: "pending" | "approved" | "rejected") => ({
  pending: { texte: tr("En attente de validation", "Awaiting approval"), ton: "soleil" },
  approved: { texte: tr("Publié sur la page d'accueil", "Published on the home page"), ton: "succes" },
  rejected: { texte: tr("Non publié", "Not published"), ton: "bulle" },
} as const)[s];

/**
 * Formulaire « Donner mon avis ». Proposé à la fin d'un épisode et sur /mon-avis.
 * `compact` : à la fin d'un épisode, n'affiche qu'une invitation tant que la personne n'a pas cliqué.
 */
export function DonnerAvis({ episodeId, compact = false }: { episodeId?: string; compact?: boolean }) {
  const qc = useQueryClient();
  const { data: avis, isLoading } = useQuery({ queryKey: ["mon-avis"], queryFn: () => api<MonAvis>("/testimonials/mine") });
  const [ouvert, setOuvert] = useState(!compact);
  const [texte, setTexte] = useState("");
  const [note, setNote] = useState(5);
  const [nom, setNom] = useState("");
  const [role, setRole] = useState("");
  const [accord, setAccord] = useState(false);

  useEffect(() => {
    if (avis) { setTexte(avis.text); setNote(avis.rating); setNom(avis.display_name); setRole(avis.role); }
  }, [avis]);

  const envoyer = useMutation({
    mutationFn: () => api<MonAvis>("/testimonials/mine", { method: "PUT", body: { text: texte, rating: note, display_name: nom, role, consent: accord, episode_id: episodeId ?? null } }),
    onSuccess: (a) => { qc.setQueryData(["mon-avis"], a); setAccord(false); if (compact) setOuvert(false); },
  });
  const retirer = useMutation({
    mutationFn: () => api("/testimonials/mine", { method: "DELETE" }),
    onSuccess: () => { qc.setQueryData(["mon-avis"], null); setTexte(""); setNom(""); setRole(""); setNote(5); },
  });

  if (isLoading) return null;

  // À la fin d'un épisode, quelqu'un qui a déjà donné son avis voit juste où il en est.
  if (compact && avis && !ouvert) {
    return (
      <Card className="mt-8 flex flex-wrap items-center gap-3">
        <span className="font-bold">{tr("Merci pour votre avis !", "Thanks for your review!")}</span>
        <Pill tone={etat(avis.status).ton}>{etat(avis.status).texte}</Pill>
        <Link to="/mon-avis" className="ml-auto font-bold text-indigo underline">{tr("Modifier", "Edit")}</Link>
      </Card>
    );
  }
  if (compact && !ouvert) {
    return (
      <Card featured className="mt-8 flex flex-wrap items-center gap-4">
        <div className="flex-1">
          <p className="font-display text-[22px] leading-[28px]">{tr("Votre épisode vous plaît ?", "Do you like your episode?")}</p>
          <p className="text-encre-douce">{tr("Dites-le en une phrase : votre avis aidera d'autres auteurs à se lancer.", "Say it in one sentence: your review will help other authors get started.")}</p>
        </div>
        <Button variant="primary" onClick={() => setOuvert(true)}>{tr("Donner mon avis", "Leave a review")}</Button>
      </Card>
    );
  }

  return (
    <Card featured={compact} className={compact ? "mt-8" : undefined}>
      <form className="flex flex-col gap-5" onSubmit={(e) => { e.preventDefault(); envoyer.mutate(); }}>
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="font-display text-[24px] leading-[30px]">{avis ? tr("Mon avis", "My review") : tr("Donner mon avis", "Leave a review")}</h2>
          {avis && <Pill tone={etat(avis.status).ton}>{etat(avis.status).texte}</Pill>}
        </div>

        <fieldset>
          <legend className="label-caps mb-2">{tr("Votre note", "Your rating")}</legend>
          <div className="flex gap-1" role="radiogroup">
            {[1, 2, 3, 4, 5].map((n) => (
              <button key={n} type="button" role="radio" aria-checked={note === n} aria-label={tr(`${n} sur 5`, `${n} out of 5`)} onClick={() => setNote(n)}
                className="inline-flex size-11 items-center justify-center rounded-[4px] hover:bg-papier">
                <Star size={28} strokeWidth={2} aria-hidden className={cn(n <= note ? "fill-soleil text-encre" : "text-trait")} />
              </button>
            ))}
          </div>
        </fieldset>

        <Field label={tr("Votre avis", "Your review")} htmlFor="avis-texte" hint={<p className="tabular text-[12px] text-encre-douce">{texte.length} / 280</p>}>
          <Textarea id="avis-texte" required minLength={10} maxLength={280} rows={3} value={texte} onChange={(e) => setTexte(e.target.value)}
            placeholder={tr("Ce que vous avez aimé, ce que vous avez créé, pour qui…", "What you liked, what you created, for whom…")} />
        </Field>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={tr("Nom affiché", "Display name")} htmlFor="avis-nom" hint={<p className="text-[12px] text-encre-douce">{tr("Ex. « Awa N. » : prénom et initiale suffisent", "E.g. “Awa N.”: first name and initial are enough")}</p>}>
            <Input id="avis-nom" required minLength={2} maxLength={60} value={nom} onChange={(e) => setNom(e.target.value)} />
          </Field>
          <Field label={tr("Qui êtes-vous ? (facultatif)", "Who are you? (optional)")} htmlFor="avis-role" hint={<p className="text-[12px] text-encre-douce">{tr("Ex. « Étudiant, Yaoundé »", "E.g. “Student, Yaoundé”")}</p>}>
            <Input id="avis-role" maxLength={80} value={role} onChange={(e) => setRole(e.target.value)} />
          </Field>
        </div>

        <label className="flex items-start gap-3">
          <input type="checkbox" required checked={accord} onChange={(e) => setAccord(e.target.checked)} className="mt-1 size-5 shrink-0 accent-vermillon" />
          <span className="text-[15px] leading-6">
            {tr("J'accepte que cet avis, avec le nom et la description ci-dessus, soit publié sur le site de MangaStudio. Je peux le retirer à tout moment depuis la page « Mon avis ».", "I agree that this review, with the name and description above, may be published on the MangaStudio website. I can remove it at any time from the “My review” page.")}
          </span>
        </label>

        <ErrorNote error={envoyer.error ?? retirer.error} />
        {envoyer.isSuccess && <p role="status" className="font-bold text-succes">{tr("Merci ! Votre avis sera publié après une rapide relecture.", "Thanks! Your review will be published after a quick check.")}</p>}

        <div className="flex flex-wrap gap-3">
          <Button type="submit" variant="primary" disabled={envoyer.isPending || !accord}>{avis ? tr("Mettre à jour", "Update") : tr("Envoyer mon avis", "Send my review")}</Button>
          {compact && <Button type="button" onClick={() => setOuvert(false)}>{tr("Plus tard", "Later")}</Button>}
          {avis && !compact && <Button type="button" disabled={retirer.isPending} onClick={() => retirer.mutate()}>{tr("Retirer mon avis", "Remove my review")}</Button>}
        </div>
        <p className="text-[13px] text-encre-douce">{tr("Votre adresse e-mail n'est jamais affichée. Toute modification repasse en relecture.", "Your email address is never shown. Any change goes back for review.")}</p>
      </form>
    </Card>
  );
}

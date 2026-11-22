import { Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Star } from "lucide-react";
import { api } from "@/lib/api";
import { Button, Card, ErrorNote, Field, Input, Pill, Textarea } from "@/components/ink";
import { cn } from "@/lib/utils";

export type MonAvis = {
  id: string; text: string; rating: number; display_name: string; role: string;
  status: "pending" | "approved" | "rejected"; created_at: string;
} | null;

const ETAT = {
  pending: { texte: "En attente de validation", ton: "soleil" },
  approved: { texte: "Publié sur la page d'accueil", ton: "succes" },
  rejected: { texte: "Non publié", ton: "bulle" },
} as const;

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
        <span className="font-bold">Merci pour votre avis !</span>
        <Pill tone={ETAT[avis.status].ton}>{ETAT[avis.status].texte}</Pill>
        <Link to="/mon-avis" className="ml-auto font-bold text-indigo underline">Modifier</Link>
      </Card>
    );
  }
  if (compact && !ouvert) {
    return (
      <Card featured className="mt-8 flex flex-wrap items-center gap-4">
        <div className="flex-1">
          <p className="font-display text-[22px] leading-[28px]">Votre épisode vous plaît ?</p>
          <p className="text-encre-douce">Dites-le en une phrase : votre avis aidera d'autres auteurs à se lancer.</p>
        </div>
        <Button variant="primary" onClick={() => setOuvert(true)}>Donner mon avis</Button>
      </Card>
    );
  }

  return (
    <Card featured={compact} className={compact ? "mt-8" : undefined}>
      <form className="flex flex-col gap-5" onSubmit={(e) => { e.preventDefault(); envoyer.mutate(); }}>
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="font-display text-[24px] leading-[30px]">{avis ? "Mon avis" : "Donner mon avis"}</h2>
          {avis && <Pill tone={ETAT[avis.status].ton}>{ETAT[avis.status].texte}</Pill>}
        </div>

        <fieldset>
          <legend className="label-caps mb-2">Votre note</legend>
          <div className="flex gap-1" role="radiogroup">
            {[1, 2, 3, 4, 5].map((n) => (
              <button key={n} type="button" role="radio" aria-checked={note === n} aria-label={`${n} sur 5`} onClick={() => setNote(n)}
                className="inline-flex size-11 items-center justify-center rounded-[4px] hover:bg-papier">
                <Star size={28} strokeWidth={2} aria-hidden className={cn(n <= note ? "fill-soleil text-encre" : "text-trait")} />
              </button>
            ))}
          </div>
        </fieldset>

        <Field label="Votre avis" htmlFor="avis-texte" hint={<p className="tabular text-[12px] text-encre-douce">{texte.length} / 280</p>}>
          <Textarea id="avis-texte" required minLength={10} maxLength={280} rows={3} value={texte} onChange={(e) => setTexte(e.target.value)}
            placeholder="Ce que vous avez aimé, ce que vous avez créé, pour qui…" />
        </Field>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Nom affiché" htmlFor="avis-nom" hint={<p className="text-[12px] text-encre-douce">Ex. « Awa N. » : prénom et initiale suffisent</p>}>
            <Input id="avis-nom" required minLength={2} maxLength={60} value={nom} onChange={(e) => setNom(e.target.value)} />
          </Field>
          <Field label="Qui êtes-vous ? (facultatif)" htmlFor="avis-role" hint={<p className="text-[12px] text-encre-douce">Ex. « Étudiant, Yaoundé »</p>}>
            <Input id="avis-role" maxLength={80} value={role} onChange={(e) => setRole(e.target.value)} />
          </Field>
        </div>

        <label className="flex items-start gap-3">
          <input type="checkbox" required checked={accord} onChange={(e) => setAccord(e.target.checked)} className="mt-1 size-5 shrink-0 accent-vermillon" />
          <span className="text-[15px] leading-6">
            J'accepte que cet avis, avec le nom et la description ci-dessus, soit publié sur le site de MangaStudio. Je peux le retirer à tout moment depuis la page « Mon avis ».
          </span>
        </label>

        <ErrorNote error={envoyer.error ?? retirer.error} />
        {envoyer.isSuccess && <p role="status" className="font-bold text-succes">Merci ! Votre avis sera publié après une rapide relecture.</p>}

        <div className="flex flex-wrap gap-3">
          <Button type="submit" variant="primary" disabled={envoyer.isPending || !accord}>{avis ? "Mettre à jour" : "Envoyer mon avis"}</Button>
          {compact && <Button type="button" onClick={() => setOuvert(false)}>Plus tard</Button>}
          {avis && !compact && <Button type="button" disabled={retirer.isPending} onClick={() => retirer.mutate()}>Retirer mon avis</Button>}
        </div>
        <p className="text-[13px] text-encre-douce">Votre adresse e-mail n'est jamais affichée. Toute modification repasse en relecture.</p>
      </form>
    </Card>
  );
}

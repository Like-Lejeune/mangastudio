import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { ChevronLeft, Heart, Trophy } from "lucide-react";
import { api } from "@/lib/api";
import { useToken } from "@/lib/session";
import { dateHeure, PHASE_TON, rangLabel, reste, type ConcoursDetail, type Participation } from "@/lib/concours";
import { titreHistoire } from "@/lib/galerie";
import { styleParId } from "@/content/styles";
import { CarteHistoire } from "@/components/galerie/CarteHistoire";
import { btnClass, Button, Card, Container, ErrorNote, Pill } from "@/components/ink";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/concours/$slug")({
  head: () => ({ meta: [{ title: "Concours — MangaStudio" }] }),
  component: PageConcours,
});

function PageConcours() {
  const { slug } = Route.useParams();
  const token = useToken();
  const { data: c, error, isLoading } = useQuery({ queryKey: ["concours", slug, !!token], queryFn: () => api<ConcoursDetail>(`/contests/${slug}`) });
  const [regles, setRegles] = useState(false);
  if (isLoading) return <Container><p className="text-encre-douce">Chargement…</p></Container>;
  if (error || !c) return <Container><ErrorNote error={error ?? new Error("Concours introuvable.")} /></Container>;
  const style = c.style ? styleParId(c.style)?.nom : null;

  return (
    <Container className="max-w-[1100px]">
      <Link to="/concours" className="mb-6 inline-flex min-h-11 items-center gap-1 font-bold hover:underline">
        <ChevronLeft size={18} strokeWidth={2.5} aria-hidden />Tous les concours
      </Link>
      <div className="flex flex-wrap items-center gap-2">
        <Pill tone={PHASE_TON[c.phase]}>{c.phase_label}</Pill>
        {style && <Pill>Style imposé : {style}</Pill>}
      </div>
      <h1 className="mt-3 font-display text-[36px] leading-[42px] sm:text-[44px] sm:leading-[50px]">{c.title}</h1>
      {c.theme && <p className="mt-2 max-w-3xl text-[19px] leading-8">{c.theme}</p>}

      <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="min-w-0">
          {c.description && <p className="whitespace-pre-line text-[17px] leading-7">{c.description}</p>}
          <dl className="mt-6 grid gap-4 sm:grid-cols-3">
            <Info t="Ouverture" v={dateHeure(c.starts_at)} />
            <Info t="Clôture" v={dateHeure(c.ends_at)} s={c.phase === "en_cours" ? `dans ${reste(c.ends_at)}` : undefined} />
            <Info t="Participants" v={String(c.entries)} />
          </dl>
          <p className="mt-6 text-[15px] leading-6 text-encre-douce">
            <b className="text-encre">Classement :</b> note du jury sur 20 (60 %) + « j'aime » reçus pendant le concours (40 %).
            {c.new_only && " Seuls les chapitres créés depuis l'ouverture du concours sont acceptés."}
            {c.max_entries > 1 ? ` Jusqu'à ${c.max_entries} histoires par participant.` : " Une histoire par participant."}
          </p>
          {c.rules && (
            <div className="mt-4">
              <button type="button" className="min-h-11 font-bold text-indigo underline" aria-expanded={regles} onClick={() => setRegles(!regles)}>
                {regles ? "Masquer le règlement" : "Lire le règlement complet"}
              </button>
              {regles && <div className="mt-2 whitespace-pre-line rounded-[4px] border-2 border-encre bg-bulle p-5 text-[15px] leading-6">{c.rules}</div>}
            </div>
          )}
        </div>

        <div className="flex flex-col gap-6">
          {c.prizes.length > 0 && (
            <Card>
              <h2 className="flex items-center gap-2 font-display text-[22px] leading-[28px]"><Trophy size={22} strokeWidth={2} aria-hidden />Les lots</h2>
              <ul className="mt-3 flex flex-col gap-2">
                {c.prizes.map((p) => <li key={p.rank} className="flex justify-between gap-3"><b className="whitespace-nowrap">{rangLabel(p.rank)}</b><span className="text-right">{p.label}</span></li>)}
              </ul>
            </Card>
          )}
          <Participer c={c} />
        </div>
      </div>

      <section className="mt-14" aria-labelledby="participants">
        <h2 id="participants" className="mb-2 font-display text-[28px] leading-[34px]">
          {c.phase === "termine" ? "Résultats" : "Les histoires en lice"}
        </h2>
        <p className="mb-6 text-encre-douce">
          {c.phase === "termine" ? "Classement final, jury et « j'aime » compris."
            : c.phase === "deliberation" ? "Le concours est clos : le jury délibère. Résultats bientôt."
            : "Lisez-les et aimez vos préférées : vos « j'aime » comptent pour 40 % du classement."}
        </p>
        {c.entries_list.length === 0 ? <p className="text-encre-douce">Aucune histoire inscrite pour l'instant.</p> : (
          <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {c.entries_list.map((e) => <li key={e.entry_id}><Participant e={e} fini={c.phase === "termine"} /></li>)}
          </ul>
        )}
      </section>
    </Container>
  );
}

function Info({ t, v, s }: { t: string; v: string; s?: string }) {
  return (
    <div className="rounded-[4px] border-2 border-encre bg-bulle p-3">
      <dt className="text-[12px] font-bold uppercase tracking-wide text-encre-douce">{t}</dt>
      <dd className="mt-1 font-bold">{v}{s && <span className="block text-[13px] font-medium text-encre-douce">{s}</span>}</dd>
    </div>
  );
}

function Participant({ e, fini }: { e: Participation; fini: boolean }) {
  return (
    <div className="flex h-full flex-col gap-2">
      {fini && e.rank && (
        <p className={cn("rounded-[4px] border-2 border-encre px-3 py-1 text-center font-bold", e.prize ? "bg-soleil" : "bg-bulle")}>
          {e.prize ? rangLabel(e.rank) : `${e.rank}e`} · <span className="tabular">{e.score?.toFixed(1)}</span>/20
        </p>
      )}
      <div className="flex-1"><CarteHistoire c={e} /></div>
      <p className="flex items-center gap-1 text-[14px] text-encre-douce">
        <Heart size={14} strokeWidth={2.5} aria-hidden /><b className="tabular text-encre">{e.contest_likes}</b> pendant le concours
        {fini && e.jury_score != null && <> · jury <b className="tabular text-encre">{e.jury_score}</b>/20</>}
      </p>
    </div>
  );
}

function Participer({ c }: { c: ConcoursDetail }) {
  const token = useToken();
  const qc = useQueryClient();
  const refresh = () => qc.invalidateQueries({ queryKey: ["concours"] });
  const inscrire = useMutation({
    mutationFn: (publication_id: string) => api(`/contests/${c.slug}/entries`, { body: { publication_id } }), onSuccess: refresh,
  });
  const retirer = useMutation({
    mutationFn: (entry_id: string) => api(`/contests/${c.slug}/entries/${entry_id}`, { method: "DELETE" }), onSuccess: refresh,
  });

  if (c.phase !== "en_cours") {
    if (!c.mine?.length) return null;
    return <Card><p className="font-bold">Votre participation est enregistrée.</p>
      {c.phase === "termine" && <p className="mt-1 text-encre-douce">Les résultats sont en bas de la page.</p>}</Card>;
  }
  if (!token) {
    return (
      <Card>
        <h2 className="font-display text-[22px] leading-[28px]">Participer</h2>
        <p className="mt-2 text-encre-douce">Créez un compte gratuit, faites votre chapitre, puis inscrivez-le ici.</p>
        <Link to="/inscription" className={cn(btnClass("primary"), "mt-4")}>Créer mon compte</Link>
      </Card>
    );
  }
  const restantes = c.max_entries - (c.mine?.length ?? 0);
  return (
    <Card>
      <h2 className="font-display text-[22px] leading-[28px]">Participer</h2>
      {c.mine && c.mine.length > 0 && (
        <ul className="mt-3 flex flex-col gap-2">
          {c.mine.map((m) => {
            const carte = c.entries_list.find((e) => e.entry_id === m.entry_id);
            return (
              <li key={m.entry_id} className="rounded-[4px] border-2 border-encre bg-papier p-3 text-[14px]">
                <b>{carte ? titreHistoire(carte) : "Votre histoire"}</b>
                <span className="block text-encre-douce">
                  {m.disqualified ? `Disqualifiée : ${m.disqualified}`
                    : m.publication_status === "published" ? "Inscrite et visible."
                    : "Inscrite. Elle apparaîtra ici dès que l'équipe l'aura publiée dans la galerie."}
                </span>
                <button className="mt-1 min-h-11 font-bold text-alerte underline" disabled={retirer.isPending}
                  onClick={() => { if (confirm("Retirer cette histoire du concours ?")) retirer.mutate(m.entry_id); }}>Retirer du concours</button>
              </li>
            );
          })}
        </ul>
      )}
      {restantes > 0 && (
        <>
          <p className="mt-3 text-[15px] leading-6 text-encre-douce">
            1. Créez un chapitre{c.style ? ` en style ${styleParId(c.style)?.nom ?? c.style}` : ""} sur le thème.<br />
            2. Sur la page de l'épisode, proposez-le à la galerie « À lire ».<br />
            3. Revenez ici pour l'inscrire.
          </p>
          {(c.eligible ?? []).length === 0 ? (
            <Link to="/" className={cn(btnClass("primary"), "mt-4")}>Créer mon chapitre</Link>
          ) : (
            <ul className="mt-4 flex flex-col gap-2">
              {c.eligible!.map((p) => (
                <li key={p.publication_id} className="rounded-[4px] border-2 border-encre p-3">
                  <p className="font-bold">{p.title}</p>
                  {p.ok ? (
                    <Button variant="primary" className="mt-2" disabled={inscrire.isPending} onClick={() => inscrire.mutate(p.publication_id)}>Inscrire cette histoire</Button>
                  ) : <p className="mt-1 text-[14px] text-encre-douce">{p.why}</p>}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
      <ErrorNote error={inscrire.error ?? retirer.error} />
    </Card>
  );
}

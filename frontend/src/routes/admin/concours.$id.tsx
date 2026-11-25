import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { dateHeure, PHASE_TON, rangLabel, type ConcoursDetail, type Participation } from "@/lib/concours";
import { titreHistoire } from "@/lib/galerie";
import { FormulaireConcours, type ConcoursIn } from "@/components/FormulaireConcours";
import { Button, Card, ErrorNote, Input, Pill } from "@/components/ink";

export const Route = createFileRoute("/admin/concours/$id")({ component: AdminUnConcours });

function AdminUnConcours() {
  const { id } = Route.useParams();
  const qc = useQueryClient();
  const [edition, setEdition] = useState(false);
  const { data: c, error } = useQuery({ queryKey: ["admin", "concours", id], queryFn: () => api<ConcoursDetail>(`/admin/contests/${id}`) });
  const refresh = () => { qc.invalidateQueries({ queryKey: ["admin"] }); qc.invalidateQueries({ queryKey: ["concours"] }); };
  const maj = useMutation({ mutationFn: (b: ConcoursIn) => api(`/admin/contests/${id}`, { method: "PUT", body: b }), onSuccess: () => { refresh(); setEdition(false); } });
  const proclamer = useMutation({ mutationFn: () => api(`/admin/contests/${id}/results`, { method: "POST" }), onSuccess: refresh });
  if (error) return <ErrorNote error={error} />;
  if (!c) return <p className="text-encre-douce">Chargement…</p>;
  const enLice = c.entries_list.filter((e) => !e.disqualified && e.publication_status === "published");
  const manquantes = enLice.filter((e) => e.jury_score == null).length;

  return (
    <>
      <Link to="/admin/concours" className="mb-4 inline-flex min-h-11 items-center font-bold hover:underline">← Tous les concours</Link>
      <div className="flex flex-wrap items-center gap-2">
        {!c.visible && <Pill tone="alerte">Brouillon</Pill>}<Pill tone={PHASE_TON[c.phase]}>{c.phase_label}</Pill>
        {c.visible && <Link to="/concours/$slug" params={{ slug: c.slug }} className="text-[14px] font-bold text-indigo underline">Voir la page publique</Link>}
      </div>
      <h2 className="mt-2 font-display text-[28px] leading-[34px]">{c.title}</h2>
      <p className="text-[14px] text-encre-douce">du {dateHeure(c.starts_at)} au {dateHeure(c.ends_at)} · {c.prizes.map((p) => `${rangLabel(p.rank)} : ${p.label}`).join(" · ") || "aucun lot"}</p>

      {!c.results_at && (
        edition ? (
          <Card className="mt-6">
            <FormulaireConcours initial={c} onSubmit={(b) => maj.mutate(b)} pending={maj.isPending} error={maj.error} submitLabel="Enregistrer" />
            <Button className="mt-3" onClick={() => setEdition(false)}>Annuler</Button>
          </Card>
        ) : <Button className="mt-4" onClick={() => setEdition(true)}>Modifier le concours</Button>
      )}

      <section className="mt-10">
        <h3 className="font-display text-[22px] leading-[28px]">Participations ({c.entries_list.length})</h3>
        <p className="mt-1 max-w-3xl text-[14px] leading-5 text-encre-douce">
          Note du jury sur 20 (60 %) + « j'aime » pendant le concours (40 %). Seules les histoires publiées dans la galerie et non disqualifiées sont classées.
          Les notes restent secrètes jusqu'à la proclamation.
        </p>
        {c.entries_list.length === 0 && <p className="mt-4 text-encre-douce">Aucune inscription pour l'instant.</p>}
        <ul className="mt-4 grid gap-4">
          {c.entries_list.map((e) => <Ligne key={e.entry_id} e={e} contestId={id} fige={!!c.results_at} onDone={refresh} />)}
        </ul>
      </section>

      {c.phase === "deliberation" && (
        <Card className="mt-10">
          <h3 className="font-display text-[22px] leading-[28px]">Proclamer les résultats</h3>
          <p className="mt-2 text-[15px] leading-6">
            Le classement de {enLice.length} histoire{enLice.length > 1 ? "s" : ""} sera calculé et figé, les lots crédités aux gagnants,
            et les résultats affichés sur la page publique. <b>C'est irréversible.</b>
          </p>
          {manquantes > 0 && <p className="mt-2 font-bold text-alerte">Il manque encore {manquantes} note{manquantes > 1 ? "s" : ""} du jury.</p>}
          <ErrorNote error={proclamer.error} />
          <Button variant="primary" className="mt-4" disabled={manquantes > 0 || proclamer.isPending}
            onClick={() => { if (confirm("Proclamer les résultats et créditer les lots ? C'est irréversible.")) proclamer.mutate(); }}>
            Proclamer les résultats
          </Button>
        </Card>
      )}
      {c.phase === "en_cours" && <p className="mt-8 text-[14px] text-encre-douce">La proclamation sera possible après la clôture ({dateHeure(c.ends_at)}).</p>}
    </>
  );
}

function Ligne({ e, contestId, fige, onDone }: { e: Participation; contestId: string; fige: boolean; onDone: () => void }) {
  const [note, setNote] = useState(e.jury_score?.toString() ?? "");
  const [motif, setMotif] = useState("");
  const m = useMutation({
    mutationFn: (b: { jury_score?: number; disqualified?: string }) => api(`/admin/contests/${contestId}/entries/${e.entry_id}`, { body: b }),
    onSuccess: onDone,
  });
  return (
    <li className="rounded-[8px] border-2 border-encre bg-bulle p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <Link to="/galerie/$id" params={{ id: e.id }} className="font-bold underline">{titreHistoire(e)}</Link>
          <p className="text-[13px] text-encre-douce">par {e.author} ({e.email}) · {e.contest_likes} « j'aime » pendant le concours</p>
          {e.publication_status !== "published" && <p className="mt-1 text-[13px] font-bold text-alerte">Pas encore publiée dans la galerie : à relire dans « Publications ».</p>}
          {e.disqualified && <p className="mt-1 text-[13px] font-bold text-alerte">Disqualifiée : {e.disqualified}</p>}
        </div>
        {fige && e.rank && <Pill tone={e.prize ? "soleil" : "bulle"}>{e.prize ? rangLabel(e.rank) : `${e.rank}e`} · {e.score}/20</Pill>}
      </div>
      {!fige && (
        <div className="mt-3 flex flex-wrap items-end gap-3">
          <form className="flex items-end gap-2" onSubmit={(ev) => { ev.preventDefault(); m.mutate({ jury_score: Number(note.replace(",", ".")) }); }}>
            <label><span className="mb-1 block text-[13px] font-bold">Note du jury /20</span>
              <Input className="w-24" inputMode="decimal" value={note} onChange={(ev) => setNote(ev.target.value)} placeholder="—" /></label>
            <Button type="submit" disabled={m.isPending || note === ""}>Enregistrer</Button>
          </form>
          {e.disqualified ? (
            <Button disabled={m.isPending} onClick={() => m.mutate({ disqualified: "" })}>Remettre en lice</Button>
          ) : (
            <form className="flex flex-wrap items-end gap-2" onSubmit={(ev) => { ev.preventDefault(); if (motif.trim().length >= 3) m.mutate({ disqualified: motif }); }}>
              <label><span className="mb-1 block text-[13px] font-bold">Motif de disqualification</span>
                <Input className="w-64" value={motif} maxLength={300} onChange={(ev) => setMotif(ev.target.value)} placeholder="Ex. : hors thème" /></label>
              <Button type="submit" disabled={m.isPending || motif.trim().length < 3}>Disqualifier</Button>
            </form>
          )}
        </div>
      )}
      <ErrorNote error={m.error} />
    </li>
  );
}

import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { CHECKPOINT_LABEL, dateTime, type ModerationEvent } from "@/lib/admin";
import { Button, Card, ErrorNote, Field, Input, Pill, Textarea } from "@/components/ink";
import { Section, selectCls, Table } from "@/components/admin";

export const Route = createFileRoute("/admin/moderation")({ component: ModerationPage });

type Term = { id: string; term: string; action: "block" | "flag" };
type Rules = { baseline: { label: string; description: string }[]; custom: { id: string; label: string; description: string; active: boolean }[] };

function ModerationPage() {
  const qc = useQueryClient();
  const refresh = () => qc.invalidateQueries({ queryKey: ["admin"] });
  const terms = useQuery({ queryKey: ["admin", "terms"], queryFn: () => api<Term[]>("/admin/terms") });
  const rules = useQuery({ queryKey: ["admin", "rules"], queryFn: () => api<Rules>("/admin/scene-rules") });
  const events = useQuery({ queryKey: ["admin", "mod-events"], queryFn: () => api<ModerationEvent[]>("/admin/moderation-events?limit=200") });

  const [term, setTerm] = useState(""); const [action, setAction] = useState("block");
  const addTerm = useMutation({ mutationFn: () => api("/admin/terms", { body: { term, action } }), onSuccess: () => { setTerm(""); refresh(); } });
  const delTerm = useMutation({ mutationFn: (id: string) => api(`/admin/terms/${id}`, { method: "DELETE" }), onSuccess: refresh });

  const [label, setLabel] = useState(""); const [description, setDescription] = useState("");
  const addRule = useMutation({ mutationFn: () => api("/admin/scene-rules", { body: { label, description, active: true } }), onSuccess: () => { setLabel(""); setDescription(""); refresh(); } });
  const toggleRule = useMutation({ mutationFn: (r: Rules["custom"][number]) => api("/admin/scene-rules", { body: { label: r.label, description: r.description, active: !r.active } }), onSuccess: refresh });
  const delRule = useMutation({ mutationFn: (id: string) => api(`/admin/scene-rules/${id}`, { method: "DELETE" }), onSuccess: refresh });

  return (
    <>
      <div className="grid gap-8 lg:grid-cols-2">
        <Section className="mt-0" title="Mots bloqués">
          <p className="mb-4 text-[14px] leading-5 text-encre-douce">
            Vérifiés sur le texte saisi et sur le scénario, sans tenir compte des accents, des majuscules ni des chiffres à la place des lettres. « Bloquer » refuse le texte ; « Signaler » l'accepte mais le note au journal.
          </p>
          <Card>
            <form className="grid gap-3 sm:grid-cols-[1fr_auto_auto] sm:items-end" onSubmit={(e) => { e.preventDefault(); addTerm.mutate(); }}>
              <Field label="Mot ou expression" htmlFor="t"><Input id="t" required minLength={2} maxLength={120} value={term} onChange={(e) => setTerm(e.target.value)} /></Field>
              <div className="flex flex-col gap-2"><label htmlFor="ta" className="label-caps">Effet</label>
                <select id="ta" className={selectCls} value={action} onChange={(e) => setAction(e.target.value)}><option value="block">Bloquer</option><option value="flag">Signaler</option></select></div>
              <Button type="submit" variant="primary" disabled={addTerm.isPending}>Ajouter</Button>
            </form>
            <div className="mt-3"><ErrorNote error={addTerm.error ?? delTerm.error ?? terms.error} /></div>
          </Card>
          <ul className="mt-4 flex flex-wrap gap-2">
            {terms.data?.length === 0 && <li className="text-encre-douce">Aucun mot pour l'instant.</li>}
            {terms.data?.map((t) => (
              <li key={t.id} className="inline-flex items-center gap-1 rounded-full border-2 border-encre bg-bulle pl-3">
                <span className="font-bold">{t.term}</span>
                <span className={`text-[12px] font-bold ${t.action === "block" ? "text-alerte" : "text-encre-douce"}`}>{t.action === "block" ? "bloqué" : "signalé"}</span>
                <button className="inline-flex size-9 items-center justify-center rounded-full hover:bg-papier" aria-label={`Retirer ${t.term}`} onClick={() => delTerm.mutate(t.id)}>
                  <Trash2 size={16} strokeWidth={2} aria-hidden />
                </button>
              </li>
            ))}
          </ul>
        </Section>

        <Section className="mt-0" title="Scènes interdites">
          <p className="mb-4 text-[14px] leading-5 text-encre-douce">
            Décrites en langage clair : le modèle les cherche dans chaque scénario avant le dessin, puis sur chaque page dessinée.
          </p>
          <Card>
            <form className="flex flex-col gap-3" onSubmit={(e) => { e.preventDefault(); addRule.mutate(); }}>
              <Field label="Libellé court" htmlFor="rl"><Input id="rl" required minLength={2} maxLength={60} value={label} onChange={(e) => setLabel(e.target.value)} placeholder="violence-graphique" /></Field>
              <Field label="Description" htmlFor="rd"><Textarea id="rd" required minLength={5} maxLength={500} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Blessure sanglante montrée en détail." /></Field>
              <Button type="submit" variant="primary" className="self-start" disabled={addRule.isPending}>Ajouter la règle</Button>
              <ErrorNote error={addRule.error ?? toggleRule.error ?? delRule.error ?? rules.error} />
            </form>
          </Card>
          <ul className="mt-4 flex flex-col gap-2">
            {rules.data?.baseline.map((r) => (
              <li key={r.label} className="rounded-[4px] border-2 border-encre bg-papier p-3">
                <div className="flex items-center gap-2"><span className="font-bold">{r.label}</span><Pill>Socle, non modifiable</Pill></div>
                <p className="mt-1 text-[14px] leading-5">{r.description}</p>
              </li>
            ))}
            {rules.data?.custom.map((r) => (
              <li key={r.id} className="rounded-[4px] border-2 border-encre bg-bulle p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-bold">{r.label}</span>
                  {r.active ? <Pill tone="succes">Active</Pill> : <Pill>Désactivée</Pill>}
                  <span className="ml-auto flex gap-2">
                    <Button className="min-h-10 px-3 text-[14px]" onClick={() => toggleRule.mutate(r)}>{r.active ? "Désactiver" : "Activer"}</Button>
                    <Button className="min-h-10 px-3" aria-label={`Supprimer ${r.label}`} onClick={() => delRule.mutate(r.id)}><Trash2 size={16} strokeWidth={2} aria-hidden /></Button>
                  </span>
                </div>
                <p className="mt-1 text-[14px] leading-5">{r.description}</p>
              </li>
            ))}
          </ul>
        </Section>
      </div>

      <Section title="Journal de modération">
        <ErrorNote error={events.error} />
        <Table head={["Quand", "Étape", "Effet", "Règle ou mot", "Utilisateur", "Extrait"]} empty={events.data?.length === 0} minWidth={900}>
          {events.data?.map((m) => (
            <tr key={m.id}>
              <td className="tabular whitespace-nowrap">{dateTime(m.created_at)}</td>
              <td>{CHECKPOINT_LABEL[m.checkpoint] ?? m.checkpoint}</td>
              <td>{m.action === "block" ? <Pill tone="alerte">Refusé</Pill> : <Pill tone="soleil">Signalé</Pill>}</td>
              <td className="font-bold">{m.rule}</td>
              <td className="break-all">{m.user_email ?? "—"}</td>
              <td className="max-w-[320px] text-[13px] text-encre-douce"><span className="line-clamp-3">{m.excerpt || "—"}</span></td>
            </tr>
          ))}
        </Table>
      </Section>
    </>
  );
}

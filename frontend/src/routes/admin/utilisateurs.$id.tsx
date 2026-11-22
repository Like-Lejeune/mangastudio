import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent, type ReactNode } from "react";
import { api } from "@/lib/api";
import { ACTION_LABEL, CHECKPOINT_LABEL, dateTime, day, INTENT_LABEL, KIND_LABEL, money, num, PLAN_LABEL, PRODUCT_LABEL, usd, type UserDetail } from "@/lib/admin";
import { useMe } from "@/lib/session";
import { Button, Card, ErrorNote, Field, Input, Pill } from "@/components/ink";
import { EpisodeStatus, Section, selectCls, Stat, Table } from "@/components/admin";

export const Route = createFileRoute("/admin/utilisateurs/$id")({ component: UserPage });

function UserPage() {
  const { id } = Route.useParams();
  const { data: me } = useMe();
  const { data: u, error, isLoading } = useQuery({ queryKey: ["admin", "user", id], queryFn: () => api<UserDetail>(`/admin/users/${id}`) });
  if (isLoading) return <p className="text-encre-douce">Chargement du compte…</p>;
  if (error || !u) return <ErrorNote error={error ?? new Error("Compte introuvable.")} />;
  const self = me?.id === u.id;

  return (
    <>
      <Link to="/admin/utilisateurs" className="inline-flex min-h-11 items-center font-bold text-indigo underline">Tous les utilisateurs</Link>
      <div className="mt-2 flex flex-wrap items-center gap-3">
        <h2 className="font-display text-[28px] leading-[34px]">{u.display_name}</h2>
        {u.is_active ? <Pill tone="succes">Actif</Pill> : <Pill tone="alerte">Suspendu</Pill>}
        {!u.email_verified && <Pill tone="soleil">E-mail non confirmé</Pill>}
        {u.is_admin && <Pill tone="indigo">Administrateur</Pill>}
      </div>
      <p className="mt-1 break-all text-encre-douce">{u.email} · inscrit le {day(u.created_at)}</p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Plan" value={u.plan.name}
          sub={u.subscription ? <>{u.subscription.status === "active" ? "Jusqu'au" : "Terminé le"} {day(u.subscription.period_end)} · {u.subscription.provider}</> : "Jamais abonné"} />
        <Stat label="Crédits" value={num(u.credits.total)} sub={<>Du mois {num(u.credits.monthly)} · packs {num(u.credits.pack)}</>} />
        <Stat label="Épisodes" value={num(u.episodes.length)} sub={<>Coût IA : {usd(u.episodes.reduce((s, e) => s + e.cost_usd, 0))}</>} />
        <Stat label="Paiements" value={num(u.payments.length)}
          sub={u.payments.length ? <>{money(u.payments.filter((p) => p.currency === "XAF").reduce((s, p) => s + p.amount, 0), "XAF")} au total</> : "Aucun"} />
      </div>

      <Section title="Actions">
        <div className="grid gap-4 lg:grid-cols-2">
          {!u.email_verified && <VerifyAction id={u.id} />}
          <CreditsAction id={u.id} />
          <PlanAction id={u.id} current={u.plan.id} />
          <StatusAction id={u.id} active={u.is_active} disabled={self} />
          <RoleAction id={u.id} isAdmin={u.is_admin} disabled={self} />
        </div>
      </Section>

      <Section title="Épisodes">
        <Table head={["Épisode", "Statut", ["Pages", "right"], ["Images", "right"], ["Coût IA", "right"], "Créé le"]} empty={u.episodes.length === 0}>
          {u.episodes.map((e) => (
            <tr key={e.id}>
              <td><Link to="/admin/episodes/$id" params={{ id: e.id }} className="font-bold underline">{e.series_title} · n° {e.number}</Link>
                {e.title && <p className="text-[13px] text-encre-douce">{e.title}</p>}</td>
              <td><EpisodeStatus status={e.status} /></td>
              <td className="tabular text-right">{e.page_count}</td>
              <td className="tabular text-right">{num(e.images)}</td>
              <td className="tabular text-right">{usd(e.cost_usd, 3)}</td>
              <td className="tabular whitespace-nowrap">{dateTime(e.created_at)}</td>
            </tr>
          ))}
        </Table>
      </Section>

      <Section title="Mouvements de crédits">
        <Table head={["Quand", "Type", ["Crédits", "right"], "Compartiment", "Motif"]} empty={u.ledger.length === 0}>
          {u.ledger.map((c) => (
            <tr key={c.id}>
              <td className="tabular whitespace-nowrap">{dateTime(c.created_at)}</td>
              <td>{KIND_LABEL[c.kind] ?? c.kind}</td>
              <td className={`tabular text-right font-bold ${c.delta < 0 ? "text-alerte" : "text-succes"}`}>{c.delta > 0 ? "+" : ""}{num(c.delta)}</td>
              <td>{c.bucket === "monthly" ? "Du mois" : "Pack"}</td>
              <td>{c.note || (c.episode_id ? "Épisode" : "—")}</td>
            </tr>
          ))}
        </Table>
      </Section>

      <Section title="Paiements">
        <Table head={["Quand", "Produit", ["Montant", "right"], "Opérateur", "État", "Référence"]} empty={u.payment_intents.length === 0 && u.payments.length === 0}>
          {u.payment_intents.map((i) => (
            <tr key={i.reference}>
              <td className="tabular whitespace-nowrap">{dateTime(i.created_at)}</td>
              <td>{PRODUCT_LABEL[i.product] ?? i.product}</td>
              <td className="tabular text-right">{money(i.amount, i.currency)}</td>
              <td>{i.operator || "—"}</td>
              <td><Pill tone={i.status === "paid" ? "succes" : i.status === "failed" ? "alerte" : "soleil"}>{INTENT_LABEL[i.status]}</Pill>
                {i.error && <p className="mt-1 text-[13px] text-encre-douce">{i.error}</p>}</td>
              <td className="tabular break-all text-[12px]">{i.reference}</td>
            </tr>
          ))}
          {u.payments.filter((p) => p.provider !== "trust").map((p) => (
            <tr key={p.id}>
              <td className="tabular whitespace-nowrap">{dateTime(p.created_at)}</td>
              <td>{PRODUCT_LABEL[p.product] ?? p.product}</td>
              <td className="tabular text-right">{money(p.amount, p.currency)}</td>
              <td>{p.provider}</td>
              <td><Pill tone="succes">Payé</Pill></td>
              <td className="tabular break-all text-[12px]">{p.external_ref}</td>
            </tr>
          ))}
        </Table>
      </Section>

      <div className="grid gap-x-8 lg:grid-cols-2">
        <Section title="Modération">
          <Table head={["Quand", "Étape", "Règle"]} empty={u.moderation_events.length === 0} minWidth={420}>
            {u.moderation_events.map((m) => (
              <tr key={m.id}>
                <td className="tabular whitespace-nowrap">{dateTime(m.created_at)}</td>
                <td>{CHECKPOINT_LABEL[m.checkpoint] ?? m.checkpoint}</td>
                <td><Pill tone={m.action === "block" ? "alerte" : "soleil"}>{m.rule}</Pill>{m.excerpt && <p className="mt-1 line-clamp-2 text-[13px] text-encre-douce">{m.excerpt}</p>}</td>
              </tr>
            ))}
          </Table>
        </Section>
        <Section title="Historique d'administration">
          <Table head={["Quand", "Action", "Détail"]} empty={u.admin_actions.length === 0} minWidth={420}>
            {u.admin_actions.map((a) => (
              <tr key={a.id}>
                <td className="tabular whitespace-nowrap">{dateTime(a.created_at)}</td>
                <td>{ACTION_LABEL[a.action] ?? a.action}</td>
                <td>{a.detail}<p className="text-[12px] text-encre-douce">par {a.admin_email}</p></td>
              </tr>
            ))}
          </Table>
        </Section>
      </div>
    </>
  );
}

/** Formulaire d'action : envoie, recharge la fiche, affiche l'erreur ou la confirmation. */
function useAction(id: string, path: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: object) => api(`/admin/users/${id}/${path}`, { body }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["admin"] }); },
  });
}

function ActionCard({ title, children, onSubmit, m, done }: { title: string; children: ReactNode; onSubmit: (e: FormEvent) => void; m: { error: unknown; isSuccess: boolean }; done: string }) {
  return (
    <Card>
      <form className="flex flex-col gap-4" onSubmit={onSubmit}>
        <h3 className="font-display text-[20px] leading-[26px]">{title}</h3>
        {children}
        <ErrorNote error={m.error} />
        {m.isSuccess && <p role="status" className="font-bold text-succes">{done}</p>}
      </form>
    </Card>
  );
}

function CreditsAction({ id }: { id: string }) {
  const [amount, setAmount] = useState("");
  const [reason, setReason] = useState("");
  const m = useAction(id, "credits");
  return (
    <ActionCard title="Ajouter ou retirer des crédits" m={m} done="Solde mis à jour."
      onSubmit={(e) => { e.preventDefault(); m.mutate({ amount: Number(amount), reason }, { onSuccess: () => { setAmount(""); setReason(""); } }); }}>
      <div className="grid gap-4 sm:grid-cols-[140px_1fr]">
        <Field label="Crédits" htmlFor="c-amount" hint={<p className="text-[12px] text-encre-douce">Négatif pour retirer</p>}>
          <Input id="c-amount" type="number" required step={1} value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="50" />
        </Field>
        <Field label="Motif" htmlFor="c-reason"><Input id="c-reason" required minLength={3} maxLength={200} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Geste commercial, correction…" /></Field>
      </div>
      <Button type="submit" variant="primary" className="self-start" disabled={m.isPending || !amount || Number(amount) === 0}>Appliquer</Button>
    </ActionCard>
  );
}

function PlanAction({ id, current }: { id: string; current: string }) {
  const [plan, setPlan] = useState(current === "free" ? "creator" : current);
  const [days, setDays] = useState("30");
  const [grant, setGrant] = useState(true);
  const [reason, setReason] = useState("");
  const m = useAction(id, "plan");
  const free = plan === "free";
  return (
    <ActionCard title="Changer le plan" m={m} done="Plan mis à jour."
      onSubmit={(e) => { e.preventDefault(); m.mutate({ plan, days: Number(days), grant_credits: grant, reason }, { onSuccess: () => setReason("") }); }}>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-2">
          <label htmlFor="p-plan" className="label-caps">Plan</label>
          <select id="p-plan" className={selectCls} value={plan} onChange={(e) => setPlan(e.target.value)}>
            {Object.entries(PLAN_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>
        {!free && <Field label="Durée (jours)" htmlFor="p-days"><Input id="p-days" type="number" min={1} max={366} required value={days} onChange={(e) => setDays(e.target.value)} /></Field>}
      </div>
      {!free && (
        <label className="flex min-h-11 items-center gap-3">
          <input type="checkbox" checked={grant} onChange={(e) => setGrant(e.target.checked)} className="size-5 accent-vermillon" />
          <span>Donner les crédits du plan (le reliquat du mois expire)</span>
        </label>
      )}
      <Field label="Motif" htmlFor="p-reason"><Input id="p-reason" required minLength={3} maxLength={200} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Partenaire, test, paiement reçu hors plateforme…" /></Field>
      <Button type="submit" variant="primary" className="self-start" disabled={m.isPending}>{free ? "Ramener au plan gratuit" : `Offrir le plan ${PLAN_LABEL[plan]}`}</Button>
    </ActionCard>
  );
}

function StatusAction({ id, active, disabled }: { id: string; active: boolean; disabled: boolean }) {
  const [reason, setReason] = useState("");
  const m = useAction(id, "status");
  return (
    <ActionCard title={active ? "Suspendre le compte" : "Réactiver le compte"} m={m} done={active ? "Compte réactivé." : "Compte suspendu."}
      onSubmit={(e) => { e.preventDefault(); m.mutate({ active: !active, reason }, { onSuccess: () => setReason("") }); }}>
      <p className="text-[14px] leading-5 text-encre-douce">
        {active ? "Le compte ne pourra plus se connecter ni utiliser la plateforme. Ses séries, crédits et paiements sont conservés." : "Le compte retrouve l'accès à la plateforme."}
      </p>
      {disabled ? <p className="font-bold">Vous ne pouvez pas suspendre votre propre compte.</p> : (
        <>
          <Field label="Motif" htmlFor="s-reason"><Input id="s-reason" required minLength={3} maxLength={200} value={reason} onChange={(e) => setReason(e.target.value)} /></Field>
          <Button type="submit" variant={active ? "secondary" : "primary"} className="self-start" disabled={m.isPending}>{active ? "Suspendre" : "Réactiver"}</Button>
        </>
      )}
    </ActionCard>
  );
}

function RoleAction({ id, isAdmin, disabled }: { id: string; isAdmin: boolean; disabled: boolean }) {
  const m = useAction(id, "role");
  const [sure, setSure] = useState(false);
  return (
    <ActionCard title="Droits d'administrateur" m={m} done="Droits mis à jour."
      onSubmit={(e) => { e.preventDefault(); m.mutate({ is_admin: !isAdmin }, { onSuccess: () => setSure(false) }); }}>
      <p className="text-[14px] leading-5 text-encre-douce">
        {isAdmin ? "Ce compte a accès à toute l'administration." : "Un administrateur voit tous les comptes, épisodes et paiements, et peut modifier crédits et plans."}
      </p>
      {disabled ? <p className="font-bold">Vous ne pouvez pas retirer vos propres droits.</p> : (
        <>
          <label className="flex min-h-11 items-center gap-3">
            <input type="checkbox" required checked={sure} onChange={(e) => setSure(e.target.checked)} className="size-5 accent-vermillon" />
            <span>{isAdmin ? "Je confirme le retrait des droits" : "Je confirme donner les droits d'administrateur"}</span>
          </label>
          <Button type="submit" className="self-start" disabled={m.isPending || !sure}>{isAdmin ? "Retirer les droits" : "Rendre administrateur"}</Button>
        </>
      )}
    </ActionCard>
  );
}

function VerifyAction({ id }: { id: string }) {
  const m = useAction(id, "verify-email");
  return (
    <ActionCard title="Confirmer l'adresse e-mail" m={m} done="Adresse confirmée, crédits offerts ajoutés."
      onSubmit={(e) => { e.preventDefault(); m.mutate({}); }}>
      <p className="text-[14px] leading-5 text-encre-douce">
        Ce compte n'a pas saisi son code. À faire seulement si vous avez vérifié l'adresse autrement (la personne vous a contacté, par exemple) : le compte reçoit alors ses crédits offerts.
      </p>
      <Button type="submit" variant="primary" className="self-start" disabled={m.isPending}>Confirmer l'adresse</Button>
    </ActionCard>
  );
}

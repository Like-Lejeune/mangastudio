import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { CHECKPOINT_LABEL, dateTime, fcfa, num, usd, type Overview } from "@/lib/admin";
import { Button, ErrorNote, Pill } from "@/components/ink";
import { DailyBars, EpisodeStatus, Section, Stat, Table } from "@/components/admin";

export const Route = createFileRoute("/admin/")({ component: OverviewPage });

function OverviewPage() {
  const { data: o, error, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["admin", "overview"], queryFn: () => api<Overview>("/admin/overview"), refetchInterval: 60_000,
  });
  if (isLoading) return <p className="text-encre-douce">Chargement des chiffres…</p>;
  if (error || !o) return <ErrorNote error={error ?? new Error("Chiffres indisponibles.")} />;

  const xaf = o.revenue["XAF"] ?? { all: 0, month: 0, count: 0 };
  const failed = (o.episodes.by_status["failed"] ?? 0) + (o.episodes.by_status["blocked"] ?? 0);
  const daily = (key: "signups" | "episodes" | "revenue_xaf" | "cost_usd") => o.daily.map((d) => ({ date: d.date, value: d[key] }));

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-[14px] text-encre-douce">Mis à jour le {dateTime(o.generated_at)} · actualisation chaque minute</p>
        <Button onClick={() => refetch()} disabled={isFetching}><RefreshCw size={18} strokeWidth={2} aria-hidden />Actualiser</Button>
      </div>

      <BudgetDuJour b={o.budget} />

      {(o.publications_pending ?? 0) > 0 && (
        <Link to="/admin/publications" className="mt-4 flex min-h-11 items-center justify-between gap-3 rounded-[4px] border-2 border-encre bg-soleil px-4 py-2 font-bold hover:underline">
          <span><span className="tabular">{o.publications_pending}</span> chapitre{(o.publications_pending ?? 0) > 1 ? "s" : ""} à relire avant publication dans la galerie</span>
          <span aria-hidden>→</span>
        </Link>
      )}

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Utilisateurs" value={num(o.users.total)} sub={<>+{num(o.users.new_7d)} en 7 j · +{num(o.users.new_30d)} en 30 j{o.users.suspended ? ` · ${o.users.suspended} suspendu(s)` : ""}</>} />
        <Stat label="Abonnés payants" value={num(o.users.paying.creator + o.users.paying.studio)} sub={<>Créateur {num(o.users.paying.creator)} · Studio {num(o.users.paying.studio)}</>} />
        <Stat label="Revenus 30 jours" value={fcfa(xaf.month)}
          sub={<>Depuis le début : {fcfa(xaf.all)} ({num(xaf.count)} paiements){o.donations?.count ? <> · Dons : {fcfa(o.donations.all)} ({num(o.donations.count)})</> : null}</>} />
        <Stat label="Coût IA 30 jours" value={usd(o.ai.cost_usd_30d)}
          sub={<>Depuis le début : {usd(o.ai.cost_usd_all)}{o.ai.cost_per_credit_usd !== null && <> · {usd(o.ai.cost_per_credit_usd, 3)} par crédit</>}</>} />
        <Stat label="Épisodes" value={num(o.episodes.total)} sub={<>{num(o.episodes.running)} en cours · {num(o.credits.images)} images dessinées</>} />
        <Stat label="Épisodes en échec" value={num(failed)} tone={failed ? "alerte" : undefined}
          sub={<>Interrompus {num(o.episodes.by_status["failed"] ?? 0)} · refusés {num(o.episodes.by_status["blocked"] ?? 0)}</>} />
        <Stat label="Crédits en circulation" value={num(o.credits.outstanding)} sub={<>Dus aux utilisateurs · {num(o.credits.debited)} déjà consommés</>} />
        <Stat label="Paiements 30 jours" value={num(o.payments.paid_30d)} tone={o.payments.pending_30d + o.payments.failed_30d ? "alerte" : undefined}
          sub={<>{num(o.payments.pending_30d)} en attente · {num(o.payments.failed_30d)} échoués</>} />
      </div>

      {o.free_credits && (
        <Section title="Crédits offerts (30 j)" aside={<span className="text-[14px]"><span className="tabular font-bold">{num(o.free_credits.total)}</span> crédits{o.ai.cost_per_credit_usd !== null && <> · environ {usd(o.free_credits.total * o.ai.cost_per_credit_usd)} de coût IA s'ils sont tous utilisés</>}</span>}>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Object.entries(o.free_credits.by_source).map(([source, n]) => <Stat key={source} label={source} value={num(n)} />)}
          </div>
        </Section>
      )}

      <Section title="Les 30 derniers jours">
        <div className="grid gap-4 md:grid-cols-2">
          <DailyBars title="Inscriptions" data={daily("signups")} format={num} />
          <DailyBars title="Épisodes lancés" data={daily("episodes")} format={num} />
          <DailyBars title="Revenus mobile money" data={daily("revenue_xaf")} format={fcfa} />
          <DailyBars title="Coût IA" data={daily("cost_usd")} format={(v) => usd(v)} />
        </div>
      </Section>

      <div className="grid gap-x-8 lg:grid-cols-2">
        <Section title="Épisodes en échec" aside={<Link to="/admin/episodes" className="font-bold text-indigo underline">Tous les épisodes</Link>}>
          <Table head={["Épisode", "Auteur", "Statut"]} empty={o.problems.length === 0} minWidth={480}>
            {o.problems.map((e) => (
              <tr key={e.id}>
                <td><Link to="/admin/episodes/$id" params={{ id: e.id }} className="font-bold underline">{e.series_title} · n° {e.number}</Link>
                  {e.error && <p className="mt-1 text-[13px] text-encre-douce">{e.error}</p>}</td>
                <td className="break-all">{e.owner_email}</td>
                <td><EpisodeStatus status={e.status} /></td>
              </tr>
            ))}
          </Table>
        </Section>
        <Section title="Modération (7 j)" aside={<span className="text-[14px]"><span className="tabular font-bold">{o.moderation.blocked_7d}</span> refus · <span className="tabular font-bold">{o.moderation.flagged_7d}</span> signalements</span>}>
          <Table head={["Quand", "Étape", "Règle", "Utilisateur"]} empty={o.moderation_events.length === 0} minWidth={480}>
            {o.moderation_events.map((m) => (
              <tr key={m.id}>
                <td className="tabular whitespace-nowrap">{dateTime(m.created_at)}</td>
                <td>{CHECKPOINT_LABEL[m.checkpoint] ?? m.checkpoint}</td>
                <td><Pill tone={m.action === "block" ? "alerte" : "soleil"}>{m.rule}</Pill></td>
                <td className="break-all">{m.user_email ?? "—"}</td>
              </tr>
            ))}
          </Table>
          <p className="mt-3"><Link to="/admin/moderation" className="font-bold text-indigo underline">Gérer la modération</Link></p>
        </Section>
      </div>
    </>
  );
}

/** Dépense IA du jour face au plafond : barre, montant et état écrit en toutes lettres. */
function BudgetDuJour({ b }: { b: Overview["budget"] }) {
  if (!b || b.limit_usd <= 0) {
    return (
      <p className="mt-6 rounded-[4px] border-2 border-dashed border-encre bg-bulle p-3 text-[14px]">
        <b>Aucun plafond de dépense IA.</b> Dépense du jour : <span className="tabular">{usd(b?.spent_today_usd ?? 0)}</span>. Réglez <code className="tabular">AI_DAILY_BUDGET_USD</code> dans le fichier .env pour limiter les coûts.
      </p>
    );
  }
  const r = b.ratio ?? 0;
  const etat = r >= 1 ? "Plafond atteint : nouveaux épisodes refusés jusqu'à demain" : r >= 0.8 ? "Proche du plafond" : "Dans le budget";
  return (
    <div className="mt-6 rounded-[8px] border-2 border-encre bg-bulle p-4 shadow-ink">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="label-caps">Dépense IA aujourd'hui</p>
        <p className={r >= 0.8 ? "font-bold text-alerte" : "font-bold text-succes"}>{etat}</p>
      </div>
      <p className="mt-1"><span className="tabular text-[24px] font-bold">{usd(b.spent_today_usd)}</span> <span className="text-encre-douce">sur {usd(b.limit_usd)} · {Math.round(r * 100)} %</span></p>
      <div className="mt-3 h-3 overflow-hidden rounded-full border-2 border-encre bg-papier" role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(Math.min(r, 1) * 100)} aria-label="Part du plafond utilisée">
        <div className={r >= 1 ? "h-full bg-alerte" : r >= 0.8 ? "h-full bg-soleil" : "h-full bg-indigo"} style={{ width: `${Math.min(r, 1) * 100}%` }} />
      </div>
    </div>
  );
}

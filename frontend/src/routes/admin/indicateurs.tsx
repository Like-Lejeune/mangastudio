import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Download } from "lucide-react";
import { api, downloadFile } from "@/lib/api";
import { Button, ErrorNote } from "@/components/ink";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/admin/indicateurs")({ component: Indicateurs });

type Fenetre = {
  signups: number; signups_verified: number; active: number; creators: number; episodes_done: number;
  revenue_xaf: number; revenue_usd: number; payers: number; ai_cost_usd: number;
  ai_cost_per_episode_usd: number | null; gross_margin_pct: number | null;
};
type Metrics = {
  generated_at: string; xaf_per_usd: number; last_30d: Fenetre; previous_30d: Fenetre; wau: number; mau: number;
  stickiness_pct: number | null; conversion_pct: number | null;
  mrr: { xaf: number; subscribers: Record<string, number>; gifted: number };
  funnel: { step: string; users: number; pct_of_signups: number | null }[];
  cohorts: { week: string; size: number; retention: (number | null)[] }[];
  referral: { referred_signups_30d: number; share_of_signups_pct: number | null; active_referrers_30d: number;
    invites_per_referrer: number | null; k_factor: number | null; qualified_pct: number | null };
  monthly: (Fenetre & { month: string })[];
  totals: { users: number; episodes_done: number; likes: number; publications: number };
};

const n = new Intl.NumberFormat("fr-FR");
const fcfa = (v: number) => `${n.format(v)} FCFA`;
const pct = (v: number | null | undefined) => (v == null ? "—" : `${n.format(v)} %`);
const mois = new Intl.DateTimeFormat("fr-FR", { month: "short", year: "numeric" });
const jour = new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "short" });

function Variation({ cur, prev }: { cur: number; prev: number }) {
  if (!prev) return <span className="text-[13px] text-encre-douce">{cur ? "nouveau" : "—"}</span>;
  const d = Math.round((100 * (cur - prev)) / prev);
  return <span className="text-[13px] font-bold text-encre-douce">{d > 0 ? "▲" : d < 0 ? "▼" : "="} {d > 0 ? "+" : ""}{d} % <span className="font-medium">vs 30 j précédents</span></span>;
}

function Tuile({ titre, valeur, sous }: { titre: string; valeur: string; sous?: React.ReactNode }) {
  return (
    <div className="rounded-[8px] border-2 border-encre bg-bulle p-4 shadow-ink">
      <p className="text-[12px] font-bold uppercase tracking-wide text-encre-douce">{titre}</p>
      <p className="tabular mt-1 font-display text-[28px] leading-[34px]">{valeur}</p>
      {sous && <div className="mt-1">{sous}</div>}
    </div>
  );
}

function Indicateurs() {
  const [telechargement, setTelechargement] = useState<unknown>(null);
  const { data: m, error, isLoading } = useQuery({ queryKey: ["admin", "metrics"], queryFn: () => api<Metrics>("/admin/metrics") });
  if (error) return <ErrorNote error={error} />;
  if (isLoading || !m) return <p className="text-encre-douce">Calcul des indicateurs…</p>;
  const c = m.last_30d, p = m.previous_30d;
  const maxFunnel = Math.max(1, ...m.funnel.map((f) => f.users));

  return (
    <>
      <p className="mb-6 max-w-3xl text-[14px] leading-5 text-encre-douce">
        Les chiffres qu'un investisseur ou un acheteur demande en premier. Calculés à partir des données existantes, sans rien modifier.
        Les comptes de l'équipe sont exclus. Une personne est <b>active</b> si elle a lancé un épisode, aimé une histoire ou payé sur la période.
      </p>

      <h2 className="mb-3 font-display text-[22px] leading-[28px]">30 derniers jours</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Tuile titre="Inscriptions" valeur={n.format(c.signups)} sous={<Variation cur={c.signups} prev={p.signups} />} />
        <Tuile titre="Utilisateurs actifs (30 j)" valeur={n.format(m.mau)} sous={<Variation cur={c.active} prev={p.active} />} />
        <Tuile titre="Actifs cette semaine" valeur={n.format(m.wau)} sous={<span className="text-[13px] text-encre-douce">soit {pct(m.stickiness_pct)} des actifs du mois</span>} />
        <Tuile titre="Épisodes terminés" valeur={n.format(c.episodes_done)} sous={<Variation cur={c.episodes_done} prev={p.episodes_done} />} />
        <Tuile titre="Chiffre d'affaires" valeur={fcfa(c.revenue_xaf)} sous={<Variation cur={c.revenue_xaf} prev={p.revenue_xaf} />} />
        <Tuile titre="Revenu récurrent mensuel" valeur={fcfa(m.mrr.xaf)}
          sous={<span className="text-[13px] text-encre-douce">{Object.entries(m.mrr.subscribers).map(([k, v]) => `${v} ${k === "creator" ? "Créateur" : "Studio"}`).join(" · ") || "aucun abonné payant"}{m.mrr.gifted ? ` · ${m.mrr.gifted} offert(s), non comptés` : ""}</span>} />
        <Tuile titre="Conversion en payants" valeur={pct(m.conversion_pct)} sous={<span className="text-[13px] text-encre-douce">des comptes confirmés, depuis le début</span>} />
        <Tuile titre="Coût IA par épisode" valeur={c.ai_cost_per_episode_usd == null ? "—" : `${c.ai_cost_per_episode_usd.toFixed(3).replace(".", ",")} $`}
          sous={<span className="text-[13px] text-encre-douce">marge brute {pct(c.gross_margin_pct)} (1 $ ≈ {m.xaf_per_usd} FCFA)</span>} />
      </div>

      <h2 className="mb-1 mt-12 font-display text-[22px] leading-[28px]">Entonnoir, depuis le début</h2>
      <p className="mb-4 text-[14px] text-encre-douce">Où les inscrits décrochent : c'est là qu'il faut agir en priorité.</p>
      <ol className="flex max-w-3xl flex-col gap-3">
        {m.funnel.map((f) => (
          <li key={f.step} className="grid grid-cols-[200px_1fr] items-center gap-3 max-sm:grid-cols-1" title={`${f.step} : ${n.format(f.users)} (${pct(f.pct_of_signups)} des inscrits)`}>
            <span className="text-[14px] font-bold">{f.step}</span>
            <span className="flex items-center gap-3">
              <span className="h-6 rounded-r-[4px] bg-indigo" style={{ width: `${Math.max(1, (100 * f.users) / maxFunnel)}%` }} aria-hidden />
              <span className="tabular whitespace-nowrap text-[14px]"><b>{n.format(f.users)}</b> <span className="text-encre-douce">· {pct(f.pct_of_signups)}</span></span>
            </span>
          </li>
        ))}
      </ol>

      <h2 className="mb-1 mt-12 font-display text-[22px] leading-[28px]">Rétention par semaine d'inscription</h2>
      <p className="mb-4 max-w-3xl text-[14px] text-encre-douce">
        Part des inscrits d'une semaine encore actifs 1, 2, 3… semaines plus tard. C'est l'indicateur le plus regardé : une rétention qui se stabilise prouve que le produit plaît.
      </p>
      <div className="overflow-x-auto rounded-[8px] border-2 border-encre bg-bulle">
        <table className="w-full min-w-[640px] text-[14px]">
          <thead>
            <tr className="border-b-2 border-encre text-left">
              <th className="p-3">Semaine du</th><th className="p-3 text-right">Inscrits</th>
              {Array.from({ length: 8 }, (_, i) => <th key={i} className="p-3 text-center">S{i}</th>)}
            </tr>
          </thead>
          <tbody>
            {m.cohorts.map((r) => (
              <tr key={r.week} className="border-b border-encre/20 last:border-0">
                <td className="p-3 font-bold">{jour.format(new Date(r.week))}</td>
                <td className="tabular p-3 text-right">{r.size}</td>
                {Array.from({ length: 8 }, (_, i) => {
                  const v = r.retention[i];
                  return (
                    <td key={i} className="tabular p-1 text-center">
                      {v == null || !r.size ? <span className="text-encre-douce">·</span> : (
                        // Une seule teinte, du clair au foncé ; plafonnée pour que le texte reste lisible.
                        <span className="block rounded-[4px] px-2 py-1" style={{ background: `color-mix(in srgb, var(--color-indigo) ${Math.round(Math.min(v, 100) * 0.45)}%, transparent)` }}
                          title={`Semaine du ${jour.format(new Date(r.week))}, S${i} : ${pct(v)} de ${r.size} inscrits`}>{Math.round(v)} %</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 className="mb-3 mt-12 font-display text-[22px] leading-[28px]">Parrainage (30 jours)</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Tuile titre="Inscrits par parrainage" valeur={n.format(m.referral.referred_signups_30d)} sous={<span className="text-[13px] text-encre-douce">{pct(m.referral.share_of_signups_pct)} des inscriptions</span>} />
        <Tuile titre="Parrains actifs" valeur={n.format(m.referral.active_referrers_30d)} sous={<span className="text-[13px] text-encre-douce">{m.referral.invites_per_referrer ?? "—"} filleul(s) chacun</span>} />
        <Tuile titre="Facteur viral (approché)" valeur={m.referral.k_factor == null ? "—" : String(m.referral.k_factor).replace(".", ",")} sous={<span className="text-[13px] text-encre-douce">filleuls par utilisateur actif ; au-dessus de 1, la croissance s'entretient seule</span>} />
        <Tuile titre="Filleuls qualifiés" valeur={pct(m.referral.qualified_pct)} sous={<span className="text-[13px] text-encre-douce">ont terminé leur 1er épisode</span>} />
      </div>

      <div className="mb-3 mt-12 flex flex-wrap items-end justify-between gap-3">
        <h2 className="font-display text-[22px] leading-[28px]">Mois par mois</h2>
        <Button onClick={() => { setTelechargement(null); downloadFile("/admin/metrics.csv", "mangastudio-indicateurs.csv").catch(setTelechargement); }}>
          <Download size={18} strokeWidth={2} aria-hidden />Télécharger (Excel, CSV)
        </Button>
      </div>
      <ErrorNote error={telechargement} />
      <div className="overflow-x-auto rounded-[8px] border-2 border-encre bg-bulle">
        <table className="w-full min-w-[760px] text-[14px]">
          <thead>
            <tr className="border-b-2 border-encre text-right">
              <th className="p-3 text-left">Mois</th><th className="p-3">Inscrits</th><th className="p-3">Actifs</th><th className="p-3">Créateurs</th>
              <th className="p-3">Épisodes</th><th className="p-3">Payeurs</th><th className="p-3">Chiffre d'affaires</th><th className="p-3">Coût IA</th>
            </tr>
          </thead>
          <tbody>
            {m.monthly.map((r, i) => (
              <tr key={r.month} className={cn("tabular border-b border-encre/20 text-right last:border-0", i === m.monthly.length - 1 && "font-bold")}>
                <td className="p-3 text-left">{mois.format(new Date(`${r.month}-01T12:00:00`))}{i === m.monthly.length - 1 && " (en cours)"}</td>
                <td className="p-3">{n.format(r.signups)}</td><td className="p-3">{n.format(r.active)}</td><td className="p-3">{n.format(r.creators)}</td>
                <td className="p-3">{n.format(r.episodes_done)}</td><td className="p-3">{n.format(r.payers)}</td>
                <td className="p-3">{fcfa(r.revenue_xaf)}{r.revenue_usd ? ` + ${n.format(r.revenue_usd)} $` : ""}</td>
                <td className="p-3">{n.format(r.ai_cost_usd)} $</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-6 text-[13px] text-encre-douce">
        Depuis le début : {n.format(m.totals.users)} inscrits, {n.format(m.totals.episodes_done)} épisodes terminés, {n.format(m.totals.likes)} « j'aime ».
        Les dons ne sont pas comptés dans le chiffre d'affaires. Calculé le {new Date(m.generated_at).toLocaleString("fr-FR")}.
      </p>
    </>
  );
}

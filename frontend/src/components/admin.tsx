import { useState, type ReactNode } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button, Pill } from "./ink";
import { ACTIVE, STATUS_LABEL } from "@/lib/api";
import { num } from "@/lib/admin";
import { cn } from "@/lib/utils";

/** Un chiffre clé, avec une ligne de contexte. */
export function Stat({ label, value, sub, tone }: { label: string; value: ReactNode; sub?: ReactNode; tone?: "alerte" }) {
  return (
    <div className="rounded-[8px] border-2 border-encre bg-bulle p-4 shadow-ink">
      <p className="label-caps">{label}</p>
      <p className={cn("tabular mt-2 text-[28px] font-bold leading-8", tone === "alerte" && "text-alerte")}>{value}</p>
      {sub && <p className="mt-1 text-[13px] leading-5 text-encre-douce">{sub}</p>}
    </div>
  );
}

export function Section({ title, aside, children, className }: { title: string; aside?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={cn("mt-10 min-w-0", className)}>
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-display text-[24px] leading-[30px]">{title}</h2>
        {aside}
      </div>
      {children}
    </section>
  );
}

/** Tableau d'administration : défile horizontalement sur petit écran, en-têtes en capitales. */
export function Table({ head, children, empty, minWidth = 720 }: { head: (string | [string, "right"])[]; children: ReactNode; empty?: boolean; minWidth?: number }) {
  return (
    <div className="overflow-x-auto rounded-[8px] border-2 border-encre bg-bulle shadow-ink">
      <table className="w-full text-[14px] leading-5" style={{ minWidth }}>
        <thead>
          <tr className="border-b-2 border-encre text-left">
            {head.map((h) => {
              const [label, align] = Array.isArray(h) ? h : [h, "left"];
              return <th key={label} className={cn("label-caps px-3 py-3", align === "right" && "text-right")}>{label}</th>;
            })}
          </tr>
        </thead>
        <tbody className="[&>tr]:border-b [&>tr]:border-trait [&>tr:last-child]:border-0 [&_td]:px-3 [&_td]:py-2.5 [&_td]:align-top">{children}</tbody>
      </table>
      {empty && <p className="px-3 py-6 text-center text-encre-douce">Rien à afficher.</p>}
    </div>
  );
}

export function Pager({ page, pages, total, onPage }: { page: number; pages: number; total: number; onPage: (p: number) => void }) {
  return (
    <div className="mt-4 flex flex-wrap items-center gap-3">
      <Button aria-label="Page précédente" disabled={page <= 1} onClick={() => onPage(page - 1)}><ChevronLeft size={20} strokeWidth={2} aria-hidden /></Button>
      <span className="tabular font-bold">{page} / {pages}</span>
      <Button aria-label="Page suivante" disabled={page >= pages} onClick={() => onPage(page + 1)}><ChevronRight size={20} strokeWidth={2} aria-hidden /></Button>
      <span className="text-[14px] text-encre-douce"><span className="tabular">{num(total)}</span> résultat{total > 1 ? "s" : ""}</span>
    </div>
  );
}

export function EpisodeStatus({ status }: { status: string }) {
  const tone = status === "done" ? "succes" : status === "failed" || status === "blocked" ? "alerte" : ACTIVE.includes(status) ? "indigo" : "bulle";
  return <Pill tone={tone}>{STATUS_LABEL[status] ?? status}</Pill>;
}

export const selectCls = "h-12 rounded-[4px] border-2 border-encre bg-blanc px-3 text-[16px] text-[#14110F]";

/**
 * Barres quotidiennes d'une seule mesure (une courbe par graphique, jamais deux échelles).
 * Survol ou focus d'une barre : la date et la valeur s'affichent. Les données restent lisibles en tableau.
 */
export function DailyBars({ title, data, format }: { title: string; data: { date: string; value: number }[]; format: (v: number) => string }) {
  const [hover, setHover] = useState<number | null>(null);
  const W = 600, H = 160, top = 8, bottom = 24;
  const max = Math.max(...data.map((d) => d.value), 0);
  const step = W / Math.max(data.length, 1);
  const bw = Math.max(2, step - 2);   // 2 px d'espace entre deux barres
  const y = (v: number) => (max ? (H - bottom - top) * (v / max) : 0);
  const label = (iso: string) => new Date(iso + "T12:00:00").toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
  const total = data.reduce((s, d) => s + d.value, 0);
  const h = hover !== null ? data[hover] : undefined;

  return (
    <figure className="m-0 rounded-[8px] border-2 border-encre bg-bulle p-4 shadow-ink">
      <figcaption className="flex items-baseline justify-between gap-2">
        <span className="font-bold">{title}</span>
        <span className="tabular text-[13px] text-encre-douce">{h ? `${label(h.date)} : ${format(h.value)}` : `30 j : ${format(total)}`}</span>
      </figcaption>
      <svg viewBox={`0 0 ${W} ${H}`} className="mt-3 block h-auto w-full" role="img" aria-label={`${title}, 30 derniers jours, total ${format(total)}`} onMouseLeave={() => setHover(null)}>
        <line x1="0" x2={W} y1={H - bottom} y2={H - bottom} stroke="var(--trait)" strokeWidth="1" />
        {max > 0 && <text x="0" y={top + 4} fontSize="11" fill="var(--encre-douce)" dominantBaseline="hanging">{format(max)}</text>}
        {data.map((d, i) => {
          const hgt = y(d.value);
          const x = i * step + 1;
          const r = Math.min(4, bw / 2, hgt);
          const yb = H - bottom;
          return (
            <g key={d.date} onMouseEnter={() => setHover(i)}>
              {/* zone de survol plus large que la barre */}
              <rect x={i * step} y={0} width={step} height={H - bottom} fill="transparent" />
              {hgt > 0 && (
                <path
                  d={`M${x},${yb} V${yb - hgt + r} Q${x},${yb - hgt} ${x + r},${yb - hgt} H${x + bw - r} Q${x + bw},${yb - hgt} ${x + bw},${yb - hgt + r} V${yb} Z`}
                  fill={hover === i ? "var(--vermillon)" : "var(--indigo)"}
                />
              )}
            </g>
          );
        })}
        {data.length > 0 && <>
          <text x="0" y={H - 6} fontSize="11" fill="var(--encre-douce)">{label(data[0]!.date)}</text>
          <text x={W} y={H - 6} fontSize="11" fill="var(--encre-douce)" textAnchor="end">{label(data[data.length - 1]!.date)}</text>
        </>}
      </svg>
      <details className="mt-2 text-[13px]">
        <summary className="cursor-pointer text-encre-douce">Voir les données</summary>
        <table className="mt-2 w-full">
          <tbody>{data.filter((d) => d.value).map((d) => <tr key={d.date}><td className="py-0.5">{label(d.date)}</td><td className="tabular text-right">{format(d.value)}</td></tr>)}</tbody>
        </table>
      </details>
    </figure>
  );
}

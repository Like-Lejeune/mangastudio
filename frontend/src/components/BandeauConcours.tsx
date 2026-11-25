import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Trophy } from "lucide-react";
import { api } from "@/lib/api";
import { dateLongue, reste, type Concours } from "@/lib/concours";

/** Annonce le concours en cours (ou le prochain). Rien s'il n'y en a pas. */
export function BandeauConcours({ className = "" }: { className?: string }) {
  const { data } = useQuery({ queryKey: ["concours"], queryFn: () => api<{ items: Concours[] }>("/contests"), staleTime: 300_000 });
  const c = data?.items.find((x) => x.phase === "en_cours") ?? data?.items.find((x) => x.phase === "a_venir");
  if (!c) return null;
  const encours = c.phase === "en_cours";
  return (
    <Link to="/concours/$slug" params={{ slug: c.slug }}
      className={`flex flex-wrap items-center gap-4 rounded-[8px] border-2 border-encre bg-soleil p-5 shadow-ink transition-transform hover:-translate-y-1 ${className}`}>
      <Trophy size={36} strokeWidth={2} aria-hidden className="shrink-0" />
      <span className="min-w-0 flex-1">
        <span className="block text-[13px] font-bold uppercase tracking-wide">{encours ? `Concours en cours · clôture dans ${reste(c.ends_at)}` : `Prochain concours · ouverture le ${dateLongue(c.starts_at)}`}</span>
        <span className="block font-display text-[24px] leading-[30px]">{c.title}</span>
        {c.prizes[0] && <span className="block text-[15px]">1er prix : {c.prizes[0].label}</span>}
      </span>
      <span className="font-bold underline">{encours ? "Participer" : "Découvrir"}</span>
    </Link>
  );
}

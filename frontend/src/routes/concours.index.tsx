import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Trophy } from "lucide-react";
import { api } from "@/lib/api";
import { dateLongue, PHASE_TON, reste, type Concours } from "@/lib/concours";
import { styleParId } from "@/content/styles";
import { Container, ErrorNote, PageTitle, Pill } from "@/components/ink";

export const Route = createFileRoute("/concours/")({
  head: () => ({
    meta: [
      { title: "Concours — MangaStudio" },
      { name: "description", content: "Participez aux concours de manga de MangaStudio : un thème, un chapitre, un jury et vos lecteurs." },
    ],
  }),
  component: ListeConcours,
});

function ListeConcours() {
  const { data, error, isLoading } = useQuery({ queryKey: ["concours"], queryFn: () => api<{ items: Concours[] }>("/contests") });
  return (
    <Container className="max-w-[1000px]">
      <PageTitle sub="Un thème, un chapitre, un jury et vos lecteurs. Des crédits et des mois de plan Studio à gagner.">Concours</PageTitle>
      <ErrorNote error={error} />
      {isLoading && <p className="text-encre-douce">Chargement…</p>}
      {data && data.items.length === 0 && (
        <div className="rounded-[8px] border-2 border-dashed border-encre bg-bulle p-8 text-center">
          <Trophy size={36} strokeWidth={2} aria-hidden className="mx-auto" />
          <p className="mt-3 font-display text-[22px] leading-[28px]">Le premier concours arrive bientôt.</p>
          <p className="mt-2 text-encre-douce">En attendant, entraînez-vous : créez un chapitre et publiez-le dans la galerie « À lire ».</p>
        </div>
      )}
      <ul className="grid gap-6">
        {data?.items.map((c) => <li key={c.id}><CarteConcours c={c} /></li>)}
      </ul>
    </Container>
  );
}

export function CarteConcours({ c }: { c: Concours }) {
  const style = c.style ? styleParId(c.style)?.nom : null;
  return (
    <Link to="/concours/$slug" params={{ slug: c.slug }}
      className="block rounded-[8px] border-2 border-encre bg-bulle p-6 shadow-ink transition-transform hover:-translate-y-1 focus-visible:-translate-y-1">
      <div className="flex flex-wrap items-center gap-2">
        <Pill tone={PHASE_TON[c.phase]}>{c.phase_label}</Pill>
        {style && <Pill>Style {style}</Pill>}
        <span className="text-[14px] text-encre-douce">du {dateLongue(c.starts_at)} au {dateLongue(c.ends_at)}</span>
      </div>
      <h2 className="mt-3 font-display text-[28px] leading-[34px]">{c.title}</h2>
      {c.theme && <p className="mt-1 text-[17px] leading-7">{c.theme}</p>}
      <div className="mt-4 flex flex-wrap gap-x-6 gap-y-1 text-[15px]">
        {c.prizes[0] && <span><Trophy size={16} strokeWidth={2.5} aria-hidden className="mr-1 inline" /><b>1er prix :</b> {c.prizes[0].label}</span>}
        <span><b className="tabular">{c.entries}</b> participant{c.entries > 1 ? "s" : ""}</span>
        {c.phase === "en_cours" && <span>Clôture dans <b>{reste(c.ends_at)}</b></span>}
        {c.phase === "a_venir" && <span>Ouverture dans <b>{reste(c.starts_at)}</b></span>}
      </div>
    </Link>
  );
}

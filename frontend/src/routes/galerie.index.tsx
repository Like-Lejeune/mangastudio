import { createFileRoute, Link } from "@tanstack/react-router";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { BookOpen } from "lucide-react";
import { api } from "@/lib/api";
import type { PageGalerie, TriGalerie } from "@/lib/galerie";
import { CarteHistoire } from "@/components/galerie/CarteHistoire";
import { Pager } from "@/components/admin";
import { btnClass, Container, ErrorNote, PageTitle } from "@/components/ink";
import { cn } from "@/lib/utils";
import { tr } from "@/lib/i18n";

const TRIS: TriGalerie[] = ["recentes", "semaine", "populaires", "coups"];
const triLabel = (t: TriGalerie) => ({
  recentes: tr("Nouveautés", "New"), semaine: tr("Les plus aimées de la semaine", "Most liked this week"),
  populaires: tr("Les plus aimées", "Most liked"), coups: tr("Coups de cœur", "Staff picks"),
})[t];

export const Route = createFileRoute("/galerie/")({
  validateSearch: (s: Record<string, unknown>): { tri?: TriGalerie; page?: number } => ({
    ...(TRIS.some((t) => t === s.tri) ? { tri: s.tri as TriGalerie } : {}),
    ...(Number(s.page) > 1 ? { page: Number(s.page) } : {}),
  }),
  head: () => ({
    meta: [
      { title: tr("À lire — les mangas de la communauté MangaStudio", "Read — manga from the MangaStudio community") },
      { name: "description", content: tr("Lisez gratuitement les chapitres de manga créés par les auteurs de MangaStudio, et aimez vos préférés.", "Read manga chapters created by MangaStudio authors for free, and like your favourites.") },
      { property: "og:title", content: tr("À lire — les mangas de la communauté MangaStudio", "Read — manga from the MangaStudio community") },
    ],
  }),
  component: Galerie,
});

function Galerie() {
  const { tri = "recentes", page = 1 } = Route.useSearch();
  const nav = Route.useNavigate();
  const { data, error, isLoading } = useQuery({
    queryKey: ["galerie", tri, page],
    queryFn: () => api<PageGalerie>(`/gallery?tri=${tri}&page=${page}&size=12`),
    placeholderData: keepPreviousData,
  });
  return (
    <Container className="max-w-[1200px]">
      <PageTitle sub={tr("Des chapitres créés par les auteurs de MangaStudio, relus par l'équipe avant publication. Lecture libre, sans compte.", "Chapters created by MangaStudio authors, reviewed by the team before publishing. Free to read, no account needed.")}>{tr("À lire", "Read")}</PageTitle>
      <div className="mb-8 flex flex-wrap gap-2" role="tablist" aria-label={tr("Trier les histoires", "Sort stories")}>
        {TRIS.map((v) => [v, triLabel(v)] as const).map(([v, l]) => (
          <button key={v} role="tab" aria-selected={tri === v} onClick={() => nav({ search: { tri: v } })}
            className={cn("min-h-11 rounded-[4px] border-2 border-encre px-4 font-bold", tri === v ? "bg-encre text-bulle" : "bg-bulle hover:bg-soleil")}>
            {l}
          </button>
        ))}
      </div>
      <ErrorNote error={error} />
      {isLoading && <p className="text-encre-douce">{tr("Chargement…", "Loading…")}</p>}
      {data && data.items.length === 0 && (
        <div className="mx-auto max-w-xl rounded-[8px] border-2 border-dashed border-encre bg-bulle p-8 text-center">
          <BookOpen size={36} strokeWidth={2} aria-hidden className="mx-auto" />
          <p className="mt-3 font-display text-[22px] leading-[28px]">
            {tri === "coups" ? tr("Pas encore de coup de cœur.", "No staff picks yet.") : tr("La galerie attend ses premières histoires.", "The gallery is waiting for its first stories.")}
          </p>
          <p className="mt-2 text-encre-douce">{tr("Créez un épisode, puis proposez-le depuis sa page : il apparaîtra ici après relecture.", "Create an episode, then submit it from its page: it will appear here after review.")}</p>
          <Link to="/" className={cn(btnClass("primary"), "mt-5")}>{tr("Créer mon manga", "Create my manga")}</Link>
        </div>
      )}
      <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {data?.items.map((c) => <li key={c.id}><CarteHistoire c={c} semaine={tri === "semaine"} /></li>)}
      </ul>
      {data && data.pages > 1 && <Pager page={data.page} pages={data.pages} total={data.total} onPage={(p) => nav({ search: { tri, page: p } })} />}
      <p className="mt-10 text-[14px] text-encre-douce">
        <Link to="/regles-publication" className="font-bold text-indigo underline">{tr("Règles de publication", "Publishing rules")}</Link>{tr(" · Un contenu vous choque ? ", " · Found something offensive? ")}
        <Link to="/contact" className="font-bold text-indigo underline">{tr("Signalez-le-nous", "Report it to us")}</Link>.
      </p>
    </Container>
  );
}

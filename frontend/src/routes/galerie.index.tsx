import { createFileRoute, Link } from "@tanstack/react-router";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { BookOpen } from "lucide-react";
import { api } from "@/lib/api";
import type { PageGalerie, TriGalerie } from "@/lib/galerie";
import { CarteHistoire } from "@/components/galerie/CarteHistoire";
import { Pager } from "@/components/admin";
import { btnClass, Container, ErrorNote, PageTitle } from "@/components/ink";
import { cn } from "@/lib/utils";

const TRIS: [TriGalerie, string][] = [["recentes", "Nouveautés"], ["semaine", "Les plus aimées de la semaine"], ["populaires", "Les plus aimées"], ["coups", "Coups de cœur"]];

export const Route = createFileRoute("/galerie/")({
  validateSearch: (s: Record<string, unknown>): { tri?: TriGalerie; page?: number } => ({
    ...(TRIS.some(([t]) => t === s.tri) ? { tri: s.tri as TriGalerie } : {}),
    ...(Number(s.page) > 1 ? { page: Number(s.page) } : {}),
  }),
  head: () => ({
    meta: [
      { title: "À lire — les mangas de la communauté MangaStudio" },
      { name: "description", content: "Lisez gratuitement les chapitres de manga créés par les auteurs de MangaStudio, et aimez vos préférés." },
      { property: "og:title", content: "À lire — les mangas de la communauté MangaStudio" },
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
      <PageTitle sub="Des chapitres créés par les auteurs de MangaStudio, relus par l'équipe avant publication. Lecture libre, sans compte.">À lire</PageTitle>
      <div className="mb-8 flex flex-wrap gap-2" role="tablist" aria-label="Trier les histoires">
        {TRIS.map(([v, l]) => (
          <button key={v} role="tab" aria-selected={tri === v} onClick={() => nav({ search: { tri: v } })}
            className={cn("min-h-11 rounded-[4px] border-2 border-encre px-4 font-bold", tri === v ? "bg-encre text-bulle" : "bg-bulle hover:bg-soleil")}>
            {l}
          </button>
        ))}
      </div>
      <ErrorNote error={error} />
      {isLoading && <p className="text-encre-douce">Chargement…</p>}
      {data && data.items.length === 0 && (
        <div className="mx-auto max-w-xl rounded-[8px] border-2 border-dashed border-encre bg-bulle p-8 text-center">
          <BookOpen size={36} strokeWidth={2} aria-hidden className="mx-auto" />
          <p className="mt-3 font-display text-[22px] leading-[28px]">
            {tri === "coups" ? "Pas encore de coup de cœur." : "La galerie attend ses premières histoires."}
          </p>
          <p className="mt-2 text-encre-douce">Créez un épisode, puis proposez-le depuis sa page : il apparaîtra ici après relecture.</p>
          <Link to="/" className={cn(btnClass("primary"), "mt-5")}>Créer mon manga</Link>
        </div>
      )}
      <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {data?.items.map((c) => <li key={c.id}><CarteHistoire c={c} semaine={tri === "semaine"} /></li>)}
      </ul>
      {data && data.pages > 1 && <Pager page={data.page} pages={data.pages} total={data.total} onPage={(p) => nav({ search: { tri, page: p } })} />}
      <p className="mt-10 text-[14px] text-encre-douce">
        <Link to="/regles-publication" className="font-bold text-indigo underline">Règles de publication</Link> · Un contenu vous choque ?{" "}
        <Link to="/contact" className="font-bold text-indigo underline">Signalez-le-nous</Link>.
      </p>
    </Container>
  );
}

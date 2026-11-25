import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PageGalerie } from "@/lib/galerie";
import { CarteHistoire } from "./CarteHistoire";
import { tr } from "@/lib/i18n";

/** Sur « Mes séries » : les histoires de la communauté. Rien n'est affiché tant qu'aucune n'est publiée. */
export function ApercuGalerie() {
  const semaine = useQuery({ queryKey: ["galerie", "apercu", "semaine"], queryFn: () => api<PageGalerie>("/gallery?tri=semaine&size=4"), staleTime: 300_000 });
  const recentes = useQuery({ queryKey: ["galerie", "apercu", "recentes"], queryFn: () => api<PageGalerie>("/gallery?tri=recentes&size=4"), staleTime: 300_000 });
  const aimees = (semaine.data?.items ?? []).filter((c) => (c.likes_week ?? 0) > 0);
  const items = aimees.length > 0 ? aimees : recentes.data?.items ?? [];
  if (items.length === 0) return null;
  return (
    <section className="mt-16" aria-labelledby="a-lire">
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="a-lire" className="font-display text-[28px] leading-[34px]">{aimees.length > 0 ? tr("Les plus aimées de la semaine", "Most liked this week") : tr("À lire sur MangaStudio", "Read on MangaStudio")}</h2>
        <Link to="/galerie" className="font-bold text-indigo underline">{tr("Toute la galerie", "Whole gallery")}</Link>
      </div>
      <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((c) => <li key={c.id}><CarteHistoire c={c} semaine={aimees.length > 0} /></li>)}
      </ul>
    </section>
  );
}

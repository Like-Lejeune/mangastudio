import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { titreHistoire, type Histoire } from "@/lib/galerie";
import { styleParId } from "@/content/styles";
import { BoutonJaime } from "@/components/galerie/BoutonJaime";
import { btnClass, Container, ErrorNote } from "@/components/ink";
import { useToken } from "@/lib/session";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/galerie/$id")({
  head: () => ({ meta: [{ title: "À lire — MangaStudio" }] }),
  component: Lecture,
});

function Lecture() {
  const { id } = Route.useParams();
  const token = useToken();
  const { data: h, error, isLoading } = useQuery({ queryKey: ["galerie", "histoire", id, !!token], queryFn: () => api<Histoire>(`/gallery/${id}`) });
  const style = h?.style ? styleParId(h.style)?.nom : undefined;

  return (
    <Container className="max-w-[900px]">
      <Link to="/galerie" className="mb-6 inline-flex min-h-11 items-center gap-1 font-bold hover:underline">
        <ChevronLeft size={18} strokeWidth={2.5} aria-hidden />Toutes les histoires
      </Link>
      {isLoading && <p className="text-encre-douce">Chargement…</p>}
      <ErrorNote error={error} />
      {h && (
        <>
          <header className="mb-8">
            {h.featured && <p className="mb-2 inline-flex items-center gap-1 rounded-full border-2 border-encre bg-soleil px-3 py-0.5 text-[13px] font-bold"><Sparkles size={14} strokeWidth={2.5} aria-hidden />Coup de cœur de l'équipe</p>}
            <h1 className="font-display text-[32px] leading-[38px] sm:text-[40px] sm:leading-[46px]">{titreHistoire(h)}</h1>
            <p className="mt-2 text-encre-douce">par <b className="text-encre">{h.author}</b>{style && <> · style {style}</>} · {h.pages} pages</p>
            {h.premise && <p className="mt-4 max-w-2xl text-[17px] leading-7">{h.premise}</p>}
            <div className="mt-5"><BoutonJaime id={h.id} likes={h.likes} liked={h.liked} mine={h.is_author} grand /></div>
          </header>
          <ol className="flex flex-col gap-6">
            {h.page_urls.map((u, i) => (
              <li key={u}><img src={u} alt={`Page ${i + 1} sur ${h.page_urls.length}`} loading={i < 2 ? "eager" : "lazy"} className="w-full rounded-[4px] border-2 border-encre bg-bulle" /></li>
            ))}
          </ol>
          <div className="mt-10 flex flex-col items-center gap-4 rounded-[8px] border-2 border-encre bg-bulle p-6 text-center shadow-ink">
            <p className="font-display text-[22px] leading-[28px]">Vous avez aimé ?</p>
            <BoutonJaime id={h.id} likes={h.likes} liked={h.liked} mine={h.is_author} grand />
            {!token && <Link to="/inscription" className={cn(btnClass("primary"))}>Créer mon manga gratuitement</Link>}
          </div>
        </>
      )}
    </Container>
  );
}

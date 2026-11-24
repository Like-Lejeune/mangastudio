import { createFileRoute, Link } from "@tanstack/react-router";
import { MISE_A_JOUR, REGLES, VALIDE } from "@/content/publication";
import { Container, PageTitle } from "@/components/ink";

export const Route = createFileRoute("/regles-publication")({
  head: () => ({ meta: [{ title: "Règles de publication — MangaStudio" }] }),
  component: Regles,
});

function Regles() {
  return (
    <Container className="max-w-[820px]">
      <PageTitle sub={`Pour publier un chapitre dans la galerie « À lire ». Mise à jour : ${MISE_A_JOUR}.`}>Règles de publication</PageTitle>
      {!VALIDE && (
        <p className="mb-8 rounded-[4px] border-2 border-encre bg-soleil p-3 text-[14px] font-medium">
          Version provisoire : ces règles peuvent encore être précisées. Les chapitres déjà publiés restent soumis à la version en vigueur.
        </p>
      )}
      <div className="flex flex-col gap-8">
        {REGLES.map((r, i) => (
          <section key={r.titre}>
            <h2 className="font-display text-[24px] leading-[30px]">{i + 1}. {r.titre}</h2>
            <ul className="mt-3 list-disc space-y-2 pl-6 text-[17px] leading-7">
              {r.points.map((p) => <li key={p}>{p}</li>)}
            </ul>
          </section>
        ))}
      </div>
      <p className="mt-10 text-encre-douce">Une question ? <Link to="/contact" className="font-bold text-indigo underline">Contactez-nous</Link>.</p>
    </Container>
  );
}

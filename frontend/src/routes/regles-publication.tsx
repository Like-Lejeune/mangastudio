import { createFileRoute, Link } from "@tanstack/react-router";
import { miseAJour, regles, VALIDE } from "@/content/publication";
import { tr } from "@/lib/i18n";
import { Container, PageTitle } from "@/components/ink";

export const Route = createFileRoute("/regles-publication")({
  head: () => ({ meta: [{ title: tr("Règles de publication — MangaStudio", "Publishing rules — MangaStudio") }] }),
  component: Regles,
});

function Regles() {
  return (
    <Container className="max-w-[820px]">
      <PageTitle sub={tr(`Pour publier un chapitre dans la galerie « À lire ». Mise à jour : ${miseAJour()}.`, `To publish a chapter in the “Read” gallery. Last updated: ${miseAJour()}.`)}>{tr("Règles de publication", "Publishing rules")}</PageTitle>
      {!VALIDE && (
        <p className="mb-8 rounded-[4px] border-2 border-encre bg-soleil p-3 text-[14px] font-medium">
          {tr("Version provisoire : ces règles peuvent encore être précisées. Les chapitres déjà publiés restent soumis à la version en vigueur.", "Provisional version: these rules may still be clarified. Chapters already published remain subject to the version in force.")}
        </p>
      )}
      <div className="flex flex-col gap-8">
        {regles().map((r, i) => (
          <section key={r.titre}>
            <h2 className="font-display text-[24px] leading-[30px]">{i + 1}. {r.titre}</h2>
            <ul className="mt-3 list-disc space-y-2 pl-6 text-[17px] leading-7">
              {r.points.map((p) => <li key={p}>{p}</li>)}
            </ul>
          </section>
        ))}
      </div>
      <p className="mt-10 text-encre-douce">{tr("Une question ? ", "A question? ")}<Link to="/contact" className="font-bold text-indigo underline">{tr("Contactez-nous", "Contact us")}</Link>.</p>
    </Container>
  );
}

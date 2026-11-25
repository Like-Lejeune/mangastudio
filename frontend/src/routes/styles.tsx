import { createFileRoute, Link } from "@tanstack/react-router";
import { stylesManga } from "@/content/styles";
import { tr } from "@/lib/i18n";
import { useToken } from "@/lib/session";
import { Container, PageTitle, Pill } from "@/components/ink";
import { VignetteStyle } from "@/components/StyleManga";
import { btnClass } from "@/components/ink";

export const Route = createFileRoute("/styles")({
  head: () => ({
    meta: [
      { title: tr("Les styles de manga — MangaStudio", "Manga styles — MangaStudio") },
      { name: "description", content: tr("Shōnen, shōjo, seinen, kodomo et afro-manga : à quoi ressemble chaque style et pour quelles histoires le choisir.", "Shōnen, shōjo, seinen, kodomo and afro-manga: what each style looks like and which stories it suits.") },
    ],
  }),
  component: StylesPage,
});

function StylesPage() {
  const token = useToken();
  return (
    <Container>
      <PageTitle sub={tr("Le style décide du trait, des visages, des cadrages et de l'ambiance de chaque page. Les exemples ci-dessous ont été dessinés par MangaStudio.", "The style sets the line work, faces, framing and mood of every page. The examples below were drawn by MangaStudio.")}>
        {tr("Quel style pour votre manga ?", "Which style for your manga?")}
      </PageTitle>
      <ul className="flex flex-col gap-10">
        {stylesManga().map((s, i) => (
          <li key={s.id} id={s.id} className="grid scroll-mt-24 items-start gap-6 rounded-[8px] border-2 border-encre bg-bulle p-5 shadow-ink md:grid-cols-[280px_1fr] md:p-6">
            <VignetteStyle style={s} legende className={`aspect-[2/3] w-full max-w-[280px] ${i % 2 ? "md:rotate-1" : "md:-rotate-1"}`} />
            <div>
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="font-display text-[32px] leading-[38px]">{s.nom}</h2>
                {s.nouveau && <Pill tone="soleil">{tr("Nouveau", "New")}</Pill>}
              </div>
              <p className="mt-1 italic text-encre-douce">{s.origine}</p>
              <p className="mt-4 text-[18px] font-bold leading-7">{s.accroche}</p>
              <p className="mt-2 leading-7">{s.description}</p>
              <p className="label-caps mt-5 mb-2">{tr("Idéal pour", "Great for")}</p>
              <ul className="flex flex-wrap gap-2">
                {s.ideal.map((x) => <li key={x} className="rounded-full border-2 border-encre bg-papier px-3 py-0.5 text-[14px] font-bold">{x}</li>)}
              </ul>
              {s.reperes && <p className="mt-4 text-[14px] text-encre-douce">{tr("Pour situer : ", "For reference: ")}{s.reperes}.</p>}
              <Link to={token ? "/" : "/inscription"} search={token ? { style: s.id } : undefined} className={`${btnClass("primary")} mt-6`}>
                {tr("Créer une série en ", "Create a series in ")}{s.nom}
              </Link>
            </div>
          </li>
        ))}
      </ul>
    </Container>
  );
}

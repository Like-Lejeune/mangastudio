import { createFileRoute, Link } from "@tanstack/react-router";
import { ChevronDown } from "lucide-react";
import { FAQ } from "@/content/faq";
import { Container, PageTitle } from "@/components/ink";

export const Route = createFileRoute("/faq")({
  head: () => ({
    meta: [
      { title: "Questions fréquentes — MangaStudio" },
      { name: "description", content: "Crédits, paiement mobile money, personnages, règles de contenu : les réponses aux questions sur MangaStudio." },
    ],
  }),
  component: FaqPage,
});

function FaqPage() {
  return (
    <Container className="max-w-[860px]">
      <PageTitle sub={<>Vous ne trouvez pas votre réponse ? <Link to="/contact" className="font-bold text-indigo underline">Écrivez-nous</Link>.</>}>
        Questions fréquentes
      </PageTitle>
      <nav aria-label="Rubriques" className="mb-10 flex flex-wrap gap-2">
        {FAQ.map((r, i) => (
          <a key={r.rubrique} href={`#rubrique-${i}`} className="inline-flex min-h-10 items-center rounded-full border-2 border-encre bg-bulle px-4 text-[14px] font-bold hover:bg-soleil">
            {r.rubrique}
          </a>
        ))}
      </nav>
      {FAQ.map((r, i) => (
        <section key={r.rubrique} id={`rubrique-${i}`} className="mb-10 scroll-mt-24">
          <h2 className="mb-4 font-display text-[24px] leading-[30px]">{r.rubrique}</h2>
          <div className="flex flex-col gap-3">
            {r.questions.map((q) => (
              <details key={q.q} className="group rounded-[8px] border-2 border-encre bg-bulle shadow-ink open:shadow-ink-lg">
                <summary className="flex min-h-14 cursor-pointer list-none items-center justify-between gap-4 px-5 py-3 font-bold [&::-webkit-details-marker]:hidden">
                  {q.q}
                  <ChevronDown size={20} strokeWidth={2} aria-hidden className="shrink-0 transition-transform group-open:rotate-180" />
                </summary>
                <p className="whitespace-pre-line border-t border-trait px-5 py-4 leading-7 text-encre-douce">{q.r}</p>
              </details>
            ))}
          </div>
        </section>
      ))}
    </Container>
  );
}

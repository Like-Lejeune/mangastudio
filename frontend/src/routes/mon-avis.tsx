import { createFileRoute } from "@tanstack/react-router";
import { Container, PageTitle, RequireAuth } from "@/components/ink";
import { DonnerAvis } from "@/components/DonnerAvis";
import { tr } from "@/lib/i18n";

export const Route = createFileRoute("/mon-avis")({
  head: () => ({ meta: [{ title: tr("Mon avis — MangaStudio", "My review — MangaStudio") }] }),
  component: () => (
    <RequireAuth>
      <Container className="max-w-[760px]">
        <PageTitle sub={tr("Votre avis apparaît sur la page d'accueil après une rapide relecture. Vous pouvez le modifier ou le retirer à tout moment.", "Your review appears on the home page after a quick check. You can edit or remove it at any time.")}>{tr("Mon avis", "My review")}</PageTitle>
        <DonnerAvis />
      </Container>
    </RequireAuth>
  ),
});

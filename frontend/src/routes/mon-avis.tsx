import { createFileRoute } from "@tanstack/react-router";
import { Container, PageTitle, RequireAuth } from "@/components/ink";
import { DonnerAvis } from "@/components/DonnerAvis";

export const Route = createFileRoute("/mon-avis")({
  head: () => ({ meta: [{ title: "Mon avis — MangaStudio" }] }),
  component: () => (
    <RequireAuth>
      <Container className="max-w-[760px]">
        <PageTitle sub="Votre avis apparaît sur la page d'accueil après une rapide relecture. Vous pouvez le modifier ou le retirer à tout moment.">Mon avis</PageTitle>
        <DonnerAvis />
      </Container>
    </RequireAuth>
  ),
});

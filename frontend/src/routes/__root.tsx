import { createRootRoute, HeadContent, Link, Outlet } from "@tanstack/react-router";
import { TopBar } from "@/components/TopBar";
import { Container } from "@/components/ink";

export const Route = createRootRoute({
  component: () => (
    <>
      <HeadContent />
      <TopBar />
      <Outlet />
    </>
  ),
  notFoundComponent: () => (
    <Container>
      <h1 className="font-display text-[32px] leading-[38px]">Page introuvable</h1>
      <p className="mt-2 text-encre-douce">Cette page n'existe pas ou n'existe plus.</p>
      <Link to="/" className="mt-4 inline-flex min-h-11 items-center font-bold text-indigo underline">Retour à l'accueil</Link>
    </Container>
  ),
});

import { createRootRoute, HeadContent, Link, Outlet } from "@tanstack/react-router";
import { TopBar } from "@/components/TopBar";
import { Footer } from "@/components/Footer";
import { Container } from "@/components/ink";
import { useLang, useT } from "@/lib/i18n";

export const Route = createRootRoute({
  component: Racine,
  notFoundComponent: Introuvable,
});

/** Changer de langue reconstruit toutes les pages : chaque texte se relit dans la nouvelle langue. */
function Racine() {
  const lang = useLang();
  return (
    <>
      <HeadContent />
      <div key={lang} className="contents">
        <TopBar />
        <Outlet />
        <Footer />
      </div>
    </>
  );
}

function Introuvable() {
  const { t } = useT();
  return (
    <Container>
      <h1 className="font-display text-[32px] leading-[38px]">{t("Page introuvable", "Page not found")}</h1>
      <p className="mt-2 text-encre-douce">{t("Cette page n'existe pas ou n'existe plus.", "This page doesn't exist or no longer exists.")}</p>
      <Link to="/" className="mt-4 inline-flex min-h-11 items-center font-bold text-indigo underline">{t("Retour à l'accueil", "Back to home")}</Link>
    </Container>
  );
}

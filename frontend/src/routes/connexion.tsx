import { createFileRoute } from "@tanstack/react-router";
import { AuthForm } from "@/components/AuthForm";
import { tr } from "@/lib/i18n";

export const Route = createFileRoute("/connexion")({
  head: () => ({ meta: [{ title: tr("Connexion — MangaStudio", "Sign in — MangaStudio") }, { name: "description", content: tr("Connectez-vous à votre studio de manga.", "Sign in to your manga studio.") }] }),
  component: () => <AuthForm mode="login" />,
});

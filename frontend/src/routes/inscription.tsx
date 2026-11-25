import { createFileRoute } from "@tanstack/react-router";
import { AuthForm } from "@/components/AuthForm";
import { tr } from "@/lib/i18n";

export const Route = createFileRoute("/inscription")({
  head: () => ({ meta: [{ title: tr("Inscription — MangaStudio", "Sign up — MangaStudio") }, { name: "description", content: tr("Créez votre compte MangaStudio et lancez votre premier épisode.", "Create your MangaStudio account and start your first episode.") }] }),
  component: () => <AuthForm mode="register" />,
});

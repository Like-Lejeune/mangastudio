import { createFileRoute } from "@tanstack/react-router";
import { AuthForm } from "@/components/AuthForm";

export const Route = createFileRoute("/inscription")({
  head: () => ({ meta: [{ title: "Inscription — MangaStudio" }, { name: "description", content: "Créez votre compte MangaStudio et lancez votre premier épisode." }] }),
  component: () => <AuthForm mode="register" />,
});

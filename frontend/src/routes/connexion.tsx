import { createFileRoute } from "@tanstack/react-router";
import { AuthForm } from "@/components/AuthForm";

export const Route = createFileRoute("/connexion")({
  head: () => ({ meta: [{ title: "Connexion — MangaStudio" }, { name: "description", content: "Connectez-vous à votre studio de manga." }] }),
  component: () => <AuthForm mode="login" />,
});

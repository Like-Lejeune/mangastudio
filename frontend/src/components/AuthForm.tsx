import { Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, tokenStore } from "@/lib/api";
import { codeRetenu, oublierCode } from "@/lib/parrainage";
import { Button, Card, ErrorNote, Field, Input } from "./ink";
import { useT } from "@/lib/i18n";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const nav = useNavigate();
  const qc = useQueryClient();
  const { t, lang } = useT();
  const [parrain] = useState(() => (mode === "register" ? codeRetenu() : null));
  const m = useMutation({
    mutationFn: () =>
      api<{ token: string; email_verified?: boolean }>(mode === "login" ? "/auth/login" : "/auth/register", {
        body: mode === "login" ? { email, password } : { email, display_name: name, password, locale: lang, ...(parrain ? { ref: parrain } : {}) },
      }),
    onSuccess: ({ token, email_verified }) => {
      qc.clear(); tokenStore.set(token);
      if (mode === "register") oublierCode();
      nav({ to: email_verified === false ? "/verifier" : "/", replace: true });
    },
  });
  const reg = mode === "register";
  return (
    <main className="flex justify-center px-4 py-12 sm:py-16">
      <Card featured className="w-full max-w-[420px]">
        <h1 className="font-display text-[32px] leading-[38px]">{reg ? t("Créer un compte", "Create an account") : t("Connexion", "Sign in")}</h1>
        <p className="mt-2 text-encre-douce">{reg ? t("Un code de confirmation vous sera envoyé par e-mail.", "We'll email you a confirmation code.") : t("Heureux de vous revoir au studio.", "Good to see you back at the studio.")}</p>
        {reg && parrain && (
          <p className="mt-4 rounded-[4px] border-2 border-encre bg-soleil px-3 py-2 text-[14px] font-bold">
            {t("Invité par un ami : +5 crédits offerts en plus, dès la confirmation de votre adresse.", "Invited by a friend: +5 extra free credits as soon as you confirm your email.")}
          </p>
        )}
        <form className="mt-6 flex flex-col gap-4" onSubmit={(e) => { e.preventDefault(); m.mutate(); }}>
          {reg && <Field label={t("Nom affiché", "Display name")} htmlFor="name"><Input id="name" required maxLength={60} value={name} onChange={(e) => setName(e.target.value)} autoComplete="nickname" /></Field>}
          <Field label={t("Adresse e-mail", "Email address")} htmlFor="email"><Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" /></Field>
          <Field label={t("Mot de passe", "Password")} htmlFor="pw" hint={reg ? <p className="text-[12px] text-encre-douce">{t("8 caractères au moins.", "At least 8 characters.")}</p> : undefined}>
            <Input id="pw" type="password" required minLength={reg ? 8 : undefined} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete={reg ? "new-password" : "current-password"} />
          </Field>
          {!reg && (
            <Link to="/mot-de-passe-oublie" className="-mt-2 self-end text-[14px] font-bold text-indigo underline">{t("Mot de passe oublié ?", "Forgot your password?")}</Link>
          )}
          <ErrorNote error={m.error} />
          <Button type="submit" variant="primary" disabled={m.isPending}>{m.isPending ? t("Un instant…", "One moment…") : reg ? t("Créer mon compte", "Create my account") : t("Se connecter", "Sign in")}</Button>
        </form>
        <p className="mt-6 text-[14px] leading-5">
          {reg ? t("Déjà inscrit ? ", "Already have an account? ") : t("Pas encore de compte ? ", "No account yet? ")}
          <Link to={reg ? "/connexion" : "/inscription"} className="inline-flex min-h-11 items-center font-bold text-indigo underline">{reg ? t("Se connecter", "Sign in") : t("Créer un compte", "Create an account")}</Link>
        </p>
      </Card>
    </main>
  );
}

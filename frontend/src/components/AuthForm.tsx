import { Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, tokenStore } from "@/lib/api";
import { codeRetenu, oublierCode } from "@/lib/parrainage";
import { Button, Card, ErrorNote, Field, Input } from "./ink";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const nav = useNavigate();
  const qc = useQueryClient();
  const [parrain] = useState(() => (mode === "register" ? codeRetenu() : null));
  const m = useMutation({
    mutationFn: () =>
      api<{ token: string; email_verified?: boolean }>(mode === "login" ? "/auth/login" : "/auth/register", {
        body: mode === "login" ? { email, password } : { email, display_name: name, password, ...(parrain ? { ref: parrain } : {}) },
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
        <h1 className="font-display text-[32px] leading-[38px]">{reg ? "Créer un compte" : "Connexion"}</h1>
        <p className="mt-2 text-encre-douce">{reg ? "Un code de confirmation vous sera envoyé par e-mail." : "Heureux de vous revoir au studio."}</p>
        {reg && parrain && (
          <p className="mt-4 rounded-[4px] border-2 border-encre bg-soleil px-3 py-2 text-[14px] font-bold">
            Invité par un ami : +5 crédits offerts en plus, dès la confirmation de votre adresse.
          </p>
        )}
        <form className="mt-6 flex flex-col gap-4" onSubmit={(e) => { e.preventDefault(); m.mutate(); }}>
          {reg && <Field label="Nom affiché" htmlFor="name"><Input id="name" required maxLength={60} value={name} onChange={(e) => setName(e.target.value)} autoComplete="nickname" /></Field>}
          <Field label="Adresse e-mail" htmlFor="email"><Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" /></Field>
          <Field label="Mot de passe" htmlFor="pw" hint={reg ? <p className="text-[12px] text-encre-douce">8 caractères au moins.</p> : undefined}>
            <Input id="pw" type="password" required minLength={reg ? 8 : undefined} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete={reg ? "new-password" : "current-password"} />
          </Field>
          {!reg && (
            <Link to="/mot-de-passe-oublie" className="-mt-2 self-end text-[14px] font-bold text-indigo underline">Mot de passe oublié ?</Link>
          )}
          <ErrorNote error={m.error} />
          <Button type="submit" variant="primary" disabled={m.isPending}>{m.isPending ? "Un instant…" : reg ? "Créer mon compte" : "Se connecter"}</Button>
        </form>
        <p className="mt-6 text-[14px] leading-5">
          {reg ? "Déjà inscrit ? " : "Pas encore de compte ? "}
          <Link to={reg ? "/connexion" : "/inscription"} className="inline-flex min-h-11 items-center font-bold text-indigo underline">{reg ? "Se connecter" : "Créer un compte"}</Link>
        </p>
      </Card>
    </main>
  );
}

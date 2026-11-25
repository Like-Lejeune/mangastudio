import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { KeyRound } from "lucide-react";
import { api, tokenStore } from "@/lib/api";
import { Button, Card, ErrorNote, Field, Input } from "@/components/ink";
import { tr } from "@/lib/i18n";

export const Route = createFileRoute("/mot-de-passe-oublie")({
  head: () => ({ meta: [{ title: tr("Mot de passe oublié — MangaStudio", "Forgot password — MangaStudio") }, { name: "robots", content: "noindex" }] }),
  component: MotDePasseOublie,
});

const ATTENTE = 60;

function MotDePasseOublie() {
  const qc = useQueryClient();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [etape, setEtape] = useState<"adresse" | "code">("adresse");
  const [code, setCode] = useState("");
  const [mdp, setMdp] = useState("");
  const [mdp2, setMdp2] = useState("");
  const [attente, setAttente] = useState(0);

  useEffect(() => {
    if (attente <= 0) return;
    const t = setTimeout(() => setAttente((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [attente]);

  const demander = useMutation({
    mutationFn: () => api("/auth/forgot-password", { body: { email } }),
    onSuccess: () => { setEtape("code"); setAttente(ATTENTE); },
  });
  const changer = useMutation({
    mutationFn: () => api<{ token: string }>("/auth/reset-password", { body: { email, code, password: mdp } }),
    onSuccess: ({ token }) => { qc.clear(); tokenStore.set(token); nav({ to: "/", replace: true }); },
  });
  const differents = mdp2.length > 0 && mdp !== mdp2;

  return (
    <main className="flex justify-center px-4 py-12 sm:py-16">
      <Card featured className="w-full max-w-[460px]">
        <KeyRound size={40} strokeWidth={2} aria-hidden className="text-vermillon" />
        <h1 className="mt-3 font-display text-[30px] leading-[36px]">{tr("Mot de passe oublié", "Forgot your password")}</h1>

        {etape === "adresse" ? (
          <>
            <p className="mt-2 text-encre-douce">{tr("Indiquez l'adresse de votre compte : nous vous envoyons un code pour choisir un nouveau mot de passe.", "Enter your account's email address: we'll send you a code to choose a new password.")}</p>
            <form className="mt-6 flex flex-col gap-4" onSubmit={(e) => { e.preventDefault(); demander.mutate(); }}>
              <Field label={tr("Adresse e-mail", "Email address")} htmlFor="email">
                <Input id="email" type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} autoFocus />
              </Field>
              <ErrorNote error={demander.error} />
              <Button type="submit" variant="primary" disabled={demander.isPending}>{demander.isPending ? tr("Envoi…", "Sending…") : tr("Recevoir un code", "Get a code")}</Button>
            </form>
          </>
        ) : (
          <>
            <p className="mt-2 text-encre-douce">
              {tr("Si un compte existe pour ", "If an account exists for ")}<b className="break-all text-encre">{email}</b>{tr(", un code à 6 chiffres vient d'y être envoyé. Pensez aux courriers indésirables.", ", a 6-digit code has just been sent to it. Remember to check your spam folder.")}
            </p>
            <form className="mt-6 flex flex-col gap-4" onSubmit={(e) => { e.preventDefault(); if (!differents) changer.mutate(); }}>
              <Field label={tr("Code reçu", "Code received")} htmlFor="code">
                <Input id="code" required inputMode="numeric" autoComplete="one-time-code" pattern="\d{6}" maxLength={6} value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  className="tabular text-center text-[28px] tracking-[0.4em]" placeholder="······" autoFocus />
              </Field>
              <Field label={tr("Nouveau mot de passe", "New password")} htmlFor="mdp" hint={<p className="text-[12px] text-encre-douce">{tr("8 caractères au moins.", "At least 8 characters.")}</p>}>
                <Input id="mdp" type="password" required minLength={8} autoComplete="new-password" value={mdp} onChange={(e) => setMdp(e.target.value)} />
              </Field>
              <Field label={tr("Le même, une seconde fois", "The same, once more")} htmlFor="mdp2">
                <Input id="mdp2" type="password" required minLength={8} autoComplete="new-password" value={mdp2} onChange={(e) => setMdp2(e.target.value)} />
              </Field>
              {differents && <p className="text-[14px] font-bold text-alerte">{tr("Les deux mots de passe sont différents.", "The two passwords don't match.")}</p>}
              <ErrorNote error={changer.error ?? demander.error} />
              <Button type="submit" variant="primary" disabled={code.length !== 6 || mdp.length < 8 || differents || changer.isPending}>
                {changer.isPending ? tr("Un instant…", "One moment…") : tr("Changer mon mot de passe", "Change my password")}
              </Button>
              <p className="text-[13px] text-encre-douce">{tr("Vous serez connecté ici, et déconnecté de vos autres appareils.", "You'll be signed in here, and signed out of your other devices.")}</p>
            </form>
            <div className="mt-6 flex flex-wrap items-center gap-3 border-t border-trait pt-4 text-[14px]">
              <Button disabled={attente > 0 || demander.isPending} onClick={() => demander.mutate()}>
                {attente > 0 ? tr(`Renvoyer le code (${attente} s)`, `Resend the code (${attente} s)`) : tr("Renvoyer le code", "Resend the code")}
              </Button>
              <button className="min-h-11 font-bold text-indigo underline" onClick={() => { setEtape("adresse"); setCode(""); changer.reset(); }}>{tr("Changer d'adresse", "Use another address")}</button>
            </div>
          </>
        )}
        <p className="mt-6 text-[14px]"><Link to="/connexion" className="inline-flex min-h-11 items-center font-bold text-indigo underline">{tr("Retour à la connexion", "Back to sign in")}</Link></p>
      </Card>
    </main>
  );
}

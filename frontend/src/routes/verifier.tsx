import { createFileRoute, Navigate, useNavigate } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { MailCheck } from "lucide-react";
import { api, tokenStore } from "@/lib/api";
import { useMe } from "@/lib/session";
import { Button, Card, ErrorNote, Field, Input, RequireAuth } from "@/components/ink";
import { tr } from "@/lib/i18n";

export const Route = createFileRoute("/verifier")({
  head: () => ({ meta: [{ title: tr("Confirmer votre adresse — MangaStudio", "Confirm your email — MangaStudio") }, { name: "robots", content: "noindex" }] }),
  component: () => <RequireAuth allowUnverified><VerifierPage /></RequireAuth>,
});

const ATTENTE = 60;   // secondes entre deux envois, comme côté serveur

function VerifierPage() {
  const { data: me } = useMe();
  const qc = useQueryClient();
  const nav = useNavigate();
  const [code, setCode] = useState("");
  const [attente, setAttente] = useState(ATTENTE);

  useEffect(() => {
    if (attente <= 0) return;
    const t = setTimeout(() => setAttente((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [attente]);

  const verifier = useMutation({
    mutationFn: () => api("/auth/verify", { body: { code } }),
    onSuccess: async () => { await qc.invalidateQueries({ queryKey: ["me"] }); nav({ to: "/", replace: true }); },
  });
  const renvoyer = useMutation({
    mutationFn: () => api("/auth/resend-code", { method: "POST" }),
    onSuccess: () => { setAttente(ATTENTE); setCode(""); verifier.reset(); },
  });

  if (me?.email_verified) return <Navigate to="/" replace />;

  return (
    <main className="flex justify-center px-4 py-12 sm:py-16">
      <Card featured className="w-full max-w-[460px]">
        <MailCheck size={40} strokeWidth={2} aria-hidden className="text-vermillon" />
        <h1 className="mt-3 font-display text-[30px] leading-[36px]">{tr("Confirmez votre adresse", "Confirm your email address")}</h1>
        <p className="mt-2 text-encre-douce">
          {tr("Nous avons envoyé un code à 6 chiffres à ", "We sent a 6-digit code to ")}<b className="break-all text-encre">{me?.email ?? tr("votre adresse", "your address")}</b>{tr(". Pensez à regarder dans les courriers indésirables.", ". Remember to check your spam folder.")}
        </p>
        <form className="mt-6 flex flex-col gap-4" onSubmit={(e) => { e.preventDefault(); verifier.mutate(); }}>
          <Field label={tr("Code reçu", "Code received")} htmlFor="code">
            <Input id="code" required inputMode="numeric" autoComplete="one-time-code" pattern="\d{6}" maxLength={6} value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
              className="tabular text-center text-[28px] tracking-[0.4em]" placeholder="······" autoFocus />
          </Field>
          <ErrorNote error={verifier.error ?? renvoyer.error} />
          {renvoyer.isSuccess && <p role="status" className="font-bold text-succes">{tr("Nouveau code envoyé.", "New code sent.")}</p>}
          <Button type="submit" variant="primary" disabled={code.length !== 6 || verifier.isPending}>{verifier.isPending ? tr("Vérification…", "Checking…") : tr("Confirmer", "Confirm")}</Button>
        </form>
        <p className="mt-4 text-[14px] text-encre-douce">{tr("Vos crédits offerts sont ajoutés dès que l'adresse est confirmée.", "Your free credits are added as soon as your address is confirmed.")}</p>
        <div className="mt-6 flex flex-wrap items-center gap-3 border-t border-trait pt-4 text-[14px]">
          <Button disabled={attente > 0 || renvoyer.isPending} onClick={() => renvoyer.mutate()}>
            {attente > 0 ? tr(`Renvoyer le code (${attente} s)`, `Resend the code (${attente} s)`) : tr("Renvoyer le code", "Resend the code")}
          </Button>
          <button className="min-h-11 font-bold text-indigo underline" onClick={() => { qc.clear(); tokenStore.set(null); nav({ to: "/inscription", replace: true }); }}>
            {tr("Mauvaise adresse ? Recommencer", "Wrong address? Start over")}
          </button>
        </div>
      </Card>
    </main>
  );
}

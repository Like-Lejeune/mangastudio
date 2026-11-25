import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { Heart, Server } from "lucide-react";
import { DONS_DIRECTS } from "@/content/contact";
import { useToken } from "@/lib/session";
import { Button, Card, Container, Field, Input, Onomatopee, PageTitle } from "@/components/ink";
import { fcfa, MobileMoneyCheckout } from "@/components/MobileMoneyCheckout";
import { cn } from "@/lib/utils";
import { tr } from "@/lib/i18n";

export const Route = createFileRoute("/soutenir")({
  head: () => ({
    meta: [
      { title: tr("Nous soutenir — MangaStudio", "Support us — MangaStudio") },
      { name: "description", content: tr("Aidez MangaStudio à payer ses serveurs et ses modèles de dessin : faites un don par mobile money.", "Help MangaStudio pay for its servers and drawing models: donate by mobile money.") },
    ],
  }),
  component: SoutenirPage,
});

const MONTANTS = [1000, 2500, 5000, 10000];
const MIN = 500, MAX = 1_000_000;

function SoutenirPage() {
  const token = useToken();
  const [choix, setChoix] = useState<number | null>(2500);
  const [libre, setLibre] = useState("");
  const [don, setDon] = useState<number | null>(null);
  const montant = choix ?? (Number(libre) || 0);
  const valide = montant >= MIN && montant <= MAX;
  const directs = [
    ["Orange Money", DONS_DIRECTS.orangeMoney],
    ["MTN Mobile Money", DONS_DIRECTS.mtnMomo],
  ] as const;
  const avecDirects = directs.some(([, d]) => d.numero);

  return (
    <Container className="max-w-[900px]">
      <PageTitle sub={tr("MangaStudio est un projet indépendant. Chaque épisode demande des serveurs et des modèles d'intelligence artificielle qui coûtent cher : vos dons nous aident à les payer, à garder des prix accessibles et une offre gratuite.", "MangaStudio is an independent project. Every episode needs servers and AI models that are expensive: your donations help us pay for them, keep prices affordable and keep a free plan.")}>
        {tr("Nous soutenir", "Support us")}
      </PageTitle>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card className="flex gap-4">
          <Server size={28} strokeWidth={2} aria-hidden className="shrink-0 text-indigo" />
          <p><b>{tr("Les serveurs", "The servers")}</b>{tr(" qui hébergent la plateforme, vos séries et vos pages, jour et nuit.", " that host the platform, your series and your pages, day and night.")}</p>
        </Card>
        <Card className="flex gap-4">
          <Heart size={28} strokeWidth={2} aria-hidden className="shrink-0 text-vermillon" />
          <p><b>{tr("Les modèles de dessin", "The drawing models")}</b>{tr(" : chaque page dessinée a un coût, que vos dons aident à couvrir.", ": every page drawn has a cost, which your donations help cover.")}</p>
        </Card>
      </div>

      <section className="mt-10">
        <h2 className="mb-4 font-display text-[24px] leading-[30px]">{tr("Faire un don par mobile money", "Donate by mobile money")}</h2>
        {don ? (
          <MobileMoneyCheckout product={{ id: "don", label: tr("Don à MangaStudio", "Donation to MangaStudio"), price: don }} onClose={() => setDon(null)}
            paidMessage={tr("Merci infiniment pour votre don ! Il nous aide à faire tourner la plateforme.", "Thank you so much for your donation! It helps us keep the platform running.")} />
        ) : (
          <Card featured className="relative">
            <Onomatopee className="absolute -top-5 right-4">{tr("MERCI !", "THANKS!")}</Onomatopee>
            <p className="label-caps mb-3">{tr("Choisissez un montant", "Choose an amount")}</p>
            <div className="flex flex-wrap gap-3">
              {MONTANTS.map((m) => (
                <button key={m} type="button" aria-pressed={choix === m} onClick={() => { setChoix(m); setLibre(""); }}
                  className={cn("tabular min-h-12 rounded-[4px] border-2 border-encre px-4 font-bold", choix === m ? "bg-encre text-bulle" : "bg-bulle hover:bg-soleil")}>
                  {fcfa(m)}
                </button>
              ))}
            </div>
            <div className="mt-4 max-w-[260px]">
              <Field label={tr("Autre montant (FCFA)", "Other amount (FCFA)")} htmlFor="libre">
                <Input id="libre" type="number" inputMode="numeric" min={MIN} max={MAX} step={100} value={libre} placeholder={tr("ex. 3000", "e.g. 3000")}
                  onChange={(e) => { setLibre(e.target.value); setChoix(null); }} />
              </Field>
            </div>
            {!valide && montant > 0 && <p className="mt-2 text-[14px] text-alerte">{tr(`Entre ${fcfa(MIN)} et ${fcfa(MAX)}.`, `Between ${fcfa(MIN)} and ${fcfa(MAX)}.`)}</p>}
            <div className="mt-6 flex flex-wrap items-center gap-4">
              {token ? (
                <Button variant="primary" disabled={!valide} onClick={() => setDon(montant)}>{tr("Donner", "Donate")} {valide ? fcfa(montant) : ""}</Button>
              ) : (
                <>
                  <Link to="/connexion" className="inline-flex min-h-12 items-center rounded-[4px] border-2 border-encre bg-vermillon px-6 font-bold text-sur-vermillon shadow-ink">{tr("Me connecter pour donner", "Sign in to donate")}</Link>
                  <span className="text-[14px] text-encre-douce">{tr("ou ", "or ")}<Link to="/inscription" className="font-bold underline">{tr("créez un compte gratuit", "create a free account")}</Link>.</span>
                </>
              )}
            </div>
            <p className="mt-4 text-[14px] leading-5 text-encre-douce">{tr("Vous validez le don sur votre téléphone (MTN ou Orange). Un don ne donne pas de crédits.", "You confirm the donation on your phone (MTN or Orange). A donation doesn't give credits.")}</p>
          </Card>
        )}
      </section>

      {avecDirects && (
        <section className="mt-10">
          <h2 className="mb-2 font-display text-[24px] leading-[30px]">{tr("Sans compte : dépôt direct", "Without an account: direct transfer")}</h2>
          <p className="mb-4 text-encre-douce">{tr("Envoyez votre don directement depuis votre téléphone. Vérifiez le nom du destinataire avant de valider.", "Send your donation directly from your phone. Check the recipient's name before confirming.")}</p>
          <div className="grid gap-4 sm:grid-cols-2">
            {directs.filter(([, d]) => d.numero).map(([nom, d]) => (
              <Card key={nom}>
                <p className="label-caps">{nom}</p>
                <p className="tabular mt-1 text-[24px] font-bold">{d.numero}</p>
                {d.titulaire && <p className="text-encre-douce">{tr("au nom de ", "in the name of ")}<b className="text-encre">{d.titulaire}</b></p>}
              </Card>
            ))}
          </div>
        </section>
      )}
    </Container>
  );
}

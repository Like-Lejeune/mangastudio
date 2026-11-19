import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { Heart, Server } from "lucide-react";
import { DONS_DIRECTS } from "@/content/contact";
import { useToken } from "@/lib/session";
import { Button, Card, Container, Field, Input, Onomatopee, PageTitle } from "@/components/ink";
import { fcfa, MobileMoneyCheckout } from "@/components/MobileMoneyCheckout";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/soutenir")({
  head: () => ({
    meta: [
      { title: "Nous soutenir — MangaStudio" },
      { name: "description", content: "Aidez MangaStudio à payer ses serveurs et ses modèles de dessin : faites un don par mobile money." },
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
      <PageTitle sub="MangaStudio est un projet indépendant. Chaque épisode demande des serveurs et des modèles d'intelligence artificielle qui coûtent cher : vos dons nous aident à les payer, à garder des prix accessibles et une offre gratuite.">
        Nous soutenir
      </PageTitle>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card className="flex gap-4">
          <Server size={28} strokeWidth={2} aria-hidden className="shrink-0 text-indigo" />
          <p><b>Les serveurs</b> qui hébergent la plateforme, vos séries et vos pages, jour et nuit.</p>
        </Card>
        <Card className="flex gap-4">
          <Heart size={28} strokeWidth={2} aria-hidden className="shrink-0 text-vermillon" />
          <p><b>Les modèles de dessin</b> : chaque page dessinée a un coût, que vos dons aident à couvrir.</p>
        </Card>
      </div>

      <section className="mt-10">
        <h2 className="mb-4 font-display text-[24px] leading-[30px]">Faire un don par mobile money</h2>
        {don ? (
          <MobileMoneyCheckout product={{ id: "don", label: "Don à MangaStudio", price: don }} onClose={() => setDon(null)}
            paidMessage="Merci infiniment pour votre don ! Il nous aide à faire tourner la plateforme." />
        ) : (
          <Card featured className="relative">
            <Onomatopee className="absolute -top-5 right-4">MERCI !</Onomatopee>
            <p className="label-caps mb-3">Choisissez un montant</p>
            <div className="flex flex-wrap gap-3">
              {MONTANTS.map((m) => (
                <button key={m} type="button" aria-pressed={choix === m} onClick={() => { setChoix(m); setLibre(""); }}
                  className={cn("tabular min-h-12 rounded-[4px] border-2 border-encre px-4 font-bold", choix === m ? "bg-encre text-bulle" : "bg-bulle hover:bg-soleil")}>
                  {fcfa(m)}
                </button>
              ))}
            </div>
            <div className="mt-4 max-w-[260px]">
              <Field label="Autre montant (FCFA)" htmlFor="libre">
                <Input id="libre" type="number" inputMode="numeric" min={MIN} max={MAX} step={100} value={libre} placeholder="ex. 3000"
                  onChange={(e) => { setLibre(e.target.value); setChoix(null); }} />
              </Field>
            </div>
            {!valide && montant > 0 && <p className="mt-2 text-[14px] text-alerte">Entre {fcfa(MIN)} et {fcfa(MAX)}.</p>}
            <div className="mt-6 flex flex-wrap items-center gap-4">
              {token ? (
                <Button variant="primary" disabled={!valide} onClick={() => setDon(montant)}>Donner {valide ? fcfa(montant) : ""}</Button>
              ) : (
                <>
                  <Link to="/connexion" className="inline-flex min-h-12 items-center rounded-[4px] border-2 border-encre bg-vermillon px-6 font-bold text-sur-vermillon shadow-ink">Me connecter pour donner</Link>
                  <span className="text-[14px] text-encre-douce">ou <Link to="/inscription" className="font-bold underline">créez un compte gratuit</Link>.</span>
                </>
              )}
            </div>
            <p className="mt-4 text-[14px] leading-5 text-encre-douce">Vous validez le don sur votre téléphone (MTN ou Orange). Un don ne donne pas de crédits.</p>
          </Card>
        )}
      </section>

      {avecDirects && (
        <section className="mt-10">
          <h2 className="mb-2 font-display text-[24px] leading-[30px]">Sans compte : dépôt direct</h2>
          <p className="mb-4 text-encre-douce">Envoyez votre don directement depuis votre téléphone. Ecrivez-nous avant d'envoyer vos dons par cette voie.</p>
          <div className="grid gap-4 sm:grid-cols-2">
            {directs.filter(([, d]) => d.numero).map(([nom, d]) => (
              <Card key={nom}>
                <p className="label-caps">{nom}</p>
                <p className="tabular mt-1 text-[24px] font-bold">{d.numero}</p>
                {d.titulaire && <p className="text-encre-douce">au nom de <b className="text-encre">{d.titulaire}</b></p>}
              </Card>
            ))}
          </div>
        </section>
      )}
    </Container>
  );
}

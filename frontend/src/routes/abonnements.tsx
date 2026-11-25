import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api, planName, type PlanOffer, type Plans } from "@/lib/api";
import { intlLocale, tr } from "@/lib/i18n";
import { useMe } from "@/lib/session";
import { Button, Card, Container, ErrorNote, Onomatopee, PageTitle, Pill, RequireAuth } from "@/components/ink";
import { fcfa, MobileMoneyCheckout as Checkout, type CheckoutProduct as Product } from "@/components/MobileMoneyCheckout";

export const Route = createFileRoute("/abonnements")({
  head: () => ({
    meta: [
      { title: tr("Abonnements — MangaStudio", "Plans — MangaStudio") },
      { name: "description", content: tr("Choisissez votre abonnement MangaStudio et payez par mobile money.", "Choose your MangaStudio plan and pay by mobile money.") },
      { property: "og:title", content: tr("Abonnements — MangaStudio", "Plans — MangaStudio") },
      { property: "og:description", content: tr("Les plans MangaStudio, payables par mobile money.", "MangaStudio plans, payable by mobile money.") },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => <RequireAuth><PlansPage /></RequireAuth>,
});

function PlansPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["plans"], queryFn: () => api<Plans>("/plans") });
  const { data: me } = useMe();
  const [product, setProduct] = useState<Product | null>(null);
  const paid = me?.plan.id !== "free";

  return (
    <Container>
      <PageTitle sub={<>
        {tr("Un crédit = une image livrée : une page, une fiche de personnage ou une couverture.", "One credit = one delivered image: a page, a character sheet or a cover.")}
        {paid && me?.subscription && <> {tr(`Votre plan ${planName(me.plan.id, me.plan.name)} court jusqu'au `, `Your ${planName(me.plan.id, me.plan.name)} plan runs until `)}<span className="tabular font-bold">{new Date(me.subscription.period_end).toLocaleDateString(intlLocale())}</span>.</>}
      </>}>{tr("Abonnements", "Plans")}</PageTitle>

      {isLoading && <p className="text-encre-douce">{tr("Chargement des plans…", "Loading plans…")}</p>}
      <ErrorNote error={error} />
      {product && <Checkout product={product} onClose={() => setProduct(null)} />}

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {data?.plans.map((p) => <PlanCard key={p.id} plan={p} current={me?.plan.id === p.id} onChoose={setProduct} />)}
      </div>

      {(data?.packs ?? (data?.pack ? [{ id: "pack" as const, ...data.pack }] : [])).length > 0 && (
        <section className="mt-12">
          <h2 className="font-display text-[28px] leading-[34px]">{tr("Packs de crédits", "Credit packs")}</h2>
          <p className="mt-1 text-encre-douce">{tr("Ils s'ajoutent à votre solde, avec ou sans abonnement, et n'expirent pas.", "They add to your balance, with or without a plan, and never expire.")}</p>
          <ul className="mt-6 grid gap-6 sm:grid-cols-3">
            {(data?.packs ?? [{ id: "pack" as const, ...data!.pack }]).map((pk, i, all) => {
              const plusGros = i === all.length - 1;
              return (
                <li key={pk.id}>
                  <Card featured={plusGros} className="relative flex h-full flex-col gap-3">
                    <Onomatopee className="absolute -top-5 right-4">+{pk.credits}</Onomatopee>
                    <h3 className="font-display text-[22px] leading-[28px]">{pk.credits} {tr("crédits", "credits")}</h3>
                    <p className="font-display text-[30px] leading-[36px]">{fcfa(pk.price_xaf)}</p>
                    <p className="tabular text-[14px] text-encre-douce">{tr(`soit ${Math.round(pk.price_xaf / pk.credits)} FCFA le crédit`, `${Math.round(pk.price_xaf / pk.credits)} FCFA per credit`)}</p>
                    <Button variant={plusGros ? "primary" : "secondary"} className="mt-auto"
                      onClick={() => setProduct({ id: pk.id, label: tr(`Pack de ${pk.credits} crédits`, `${pk.credits}-credit pack`), price: pk.price_xaf })}>
                      {tr("Acheter", "Buy")}
                    </Button>
                  </Card>
                </li>
              );
            })}
          </ul>
        </section>
      )}
      <p className="mt-8 text-[14px] leading-5 text-encre-douce">
        {tr("Paiement par mobile money : vous validez chaque paiement sur votre téléphone. Un plan payé est actif 30 jours, sans prélèvement automatique.", "Payment by mobile money: you confirm each payment on your phone. A paid plan is active for 30 days, with no automatic charge.")}
      </p>
    </Container>
  );
}

function PlanCard({ plan: p, current, onChoose }: { plan: PlanOffer; current: boolean; onChoose: (p: Product) => void }) {
  const free = p.price_xaf === 0;
  const nom = planName(p.id, p.name);
  return (
    <Card featured={current} className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-2">
        <h2 className="font-display text-[24px] leading-[30px]">{nom}</h2>
        {current && <Pill tone="succes">{tr("Plan actuel", "Current plan")}</Pill>}
      </div>
      <p className="font-display text-[32px] leading-[38px]">
        {free ? tr("Gratuit", "Free") : fcfa(p.price_xaf)}
        {!free && <span className="block font-sans text-[14px] font-medium leading-5 text-encre-douce">{tr("pour 30 jours", "for 30 days")}</span>}
      </p>
      <ul className="flex flex-1 flex-col gap-2 text-[14px] leading-5">
        <li><span className="tabular font-bold">{p.credits}</span> {free ? tr("crédits offerts à l'inscription", "free credits when you sign up") : tr("crédits par période", "credits per period")}</li>
        <li>{tr("Jusqu'à ", "Up to ")}<span className="tabular font-bold">{p.max_characters}</span>{tr(" personnages par épisode", " characters per episode")}</li>
        <li>{tr("Jusqu'à ", "Up to ")}<span className="tabular font-bold">{p.max_pages}</span>{tr(" pages par épisode", " pages per episode")}</li>
        <li>{p.color ? tr("Couleur et noir et blanc", "Colour and black & white") : tr("Noir et blanc", "Black & white")}</li>
        <li>{tr("Redessin d'une page : ", "Page redraw: ")}{p.redraw ? tr("inclus", "included") : tr("non inclus", "not included")}</li>
      </ul>
      {free ? (
        <p className="min-h-12 text-[14px] leading-5 text-encre-douce">{tr("Le plan de départ, sans paiement.", "The starter plan, no payment.")}</p>
      ) : (
        <Button variant={current ? "secondary" : "primary"} onClick={() => onChoose({ id: p.id as "creator" | "studio", label: tr(`Plan ${nom}`, `${nom} plan`), price: p.price_xaf })}>
          {current ? tr("Renouveler pour 30 jours", "Renew for 30 days") : tr(`Choisir ${nom}`, `Choose ${nom}`)}
        </Button>
      )}
    </Card>
  );
}

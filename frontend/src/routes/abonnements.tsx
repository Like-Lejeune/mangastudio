import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api, type PlanOffer, type Plans } from "@/lib/api";
import { useMe } from "@/lib/session";
import { Button, Card, Container, ErrorNote, Onomatopee, PageTitle, Pill, RequireAuth } from "@/components/ink";
import { fcfa, MobileMoneyCheckout as Checkout, type CheckoutProduct as Product } from "@/components/MobileMoneyCheckout";

export const Route = createFileRoute("/abonnements")({
  head: () => ({
    meta: [
      { title: "Abonnements — MangaStudio" },
      { name: "description", content: "Choisissez votre abonnement MangaStudio et payez par mobile money." },
      { property: "og:title", content: "Abonnements — MangaStudio" },
      { property: "og:description", content: "Les plans MangaStudio, payables par mobile money." },
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
        Un crédit = une image livrée : une page, une fiche de personnage ou une couverture.
        {paid && me?.subscription && <> Votre plan {me.plan.name} court jusqu'au <span className="tabular font-bold">{new Date(me.subscription.period_end).toLocaleDateString("fr-FR")}</span>.</>}
      </>}>Abonnements</PageTitle>

      {isLoading && <p className="text-encre-douce">Chargement des plans…</p>}
      <ErrorNote error={error} />
      {product && <Checkout product={product} onClose={() => setProduct(null)} />}

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {data?.plans.map((p) => <PlanCard key={p.id} plan={p} current={me?.plan.id === p.id} onChoose={setProduct} />)}
      </div>

      {data?.pack && (
        <Card featured className="relative mt-12 flex flex-col gap-4 sm:flex-row sm:items-center">
          <Onomatopee className="absolute -top-5 right-4">+{data.pack.credits}</Onomatopee>
          <div className="flex-1">
            <h2 className="font-display text-[24px] leading-[30px]">Pack de {data.pack.credits} crédits</h2>
            <p className="text-encre-douce">Ces crédits s'ajoutent à votre solde et n'expirent pas.</p>
          </div>
          <p className="font-display text-[32px] leading-[38px]">{fcfa(data.pack.price_xaf)}</p>
          <Button variant="primary" onClick={() => setProduct({ id: "pack", label: `Pack de ${data.pack.credits} crédits`, price: data.pack.price_xaf })}>Acheter le pack</Button>
        </Card>
      )}
      <p className="mt-8 text-[14px] leading-5 text-encre-douce">
        Paiement par mobile money : vous validez chaque paiement sur votre téléphone. Un plan payé est actif 30 jours, sans prélèvement automatique.
      </p>
    </Container>
  );
}

function PlanCard({ plan: p, current, onChoose }: { plan: PlanOffer; current: boolean; onChoose: (p: Product) => void }) {
  const free = p.price_xaf === 0;
  return (
    <Card featured={current} className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-2">
        <h2 className="font-display text-[24px] leading-[30px]">{p.name}</h2>
        {current && <Pill tone="succes">Plan actuel</Pill>}
      </div>
      <p className="font-display text-[32px] leading-[38px]">
        {free ? "Gratuit" : fcfa(p.price_xaf)}
        {!free && <span className="block font-sans text-[14px] font-medium leading-5 text-encre-douce">pour 30 jours</span>}
      </p>
      <ul className="flex flex-1 flex-col gap-2 text-[14px] leading-5">
        <li><span className="tabular font-bold">{p.credits}</span> {free ? "crédits offerts à l'inscription" : "crédits par période"}</li>
        <li>Jusqu'à <span className="tabular font-bold">{p.max_characters}</span> personnages par épisode</li>
        <li>Jusqu'à <span className="tabular font-bold">{p.max_pages}</span> pages par épisode</li>
        <li>{p.color ? "Couleur et noir et blanc" : "Noir et blanc"}</li>
        <li>Redessin d'une page : {p.redraw ? "inclus" : "non inclus"}</li>
      </ul>
      {free ? (
        <p className="min-h-12 text-[14px] leading-5 text-encre-douce">Le plan de départ, sans paiement.</p>
      ) : (
        <Button variant={current ? "secondary" : "primary"} onClick={() => onChoose({ id: p.id as "creator" | "studio", label: `Plan ${p.name}`, price: p.price_xaf })}>
          {current ? "Renouveler pour 30 jours" : `Choisir ${p.name}`}
        </Button>
      )}
    </Card>
  );
}

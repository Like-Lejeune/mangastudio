import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Check, Loader, X } from "lucide-react";
import { api, type Payment, type PlanOffer, type Plans } from "@/lib/api";
import { useMe } from "@/lib/session";
import { Button, Card, Container, ErrorNote, Field, Input, Onomatopee, PageTitle, Pill, RequireAuth } from "@/components/ink";

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

const fcfa = (n: number) => `${n.toLocaleString("fr-FR")} FCFA`;
const POLL_MS = 3000;
const WAIT_MAX_MS = 3 * 60 * 1000;

type Product = { id: "creator" | "studio" | "pack"; label: string; price: number };
type Operator = { code: string; name: string };

/** La forme exacte de la liste TrustChange n'est pas figée : on accepte un tableau ou un objet qui en contient un. */
function readOperators(data: unknown): Operator[] {
  const list = Array.isArray(data) ? data : Object.values((data ?? {}) as Record<string, unknown>).find(Array.isArray) ?? [];
  return (list as Record<string, unknown>[])
    .map((o) => {
      const code = String(o["paymentCode"] ?? o["code"] ?? o["id"] ?? "");
      return { code, name: String(o["name"] ?? o["label"] ?? o["operator"] ?? code) };
    })
    .filter((o) => o.code);
}

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

/** Paiement mobile money : opérateur et numéro, puis attente de la validation sur le téléphone. */
function Checkout({ product, onClose }: { product: Product; onClose: () => void }) {
  const qc = useQueryClient();
  const operators = useQuery({ queryKey: ["operators"], queryFn: async () => readOperators(await api<unknown>("/billing/operators")), staleTime: 10 * 60 * 1000 });
  const [operator, setOperator] = useState("");
  const [phone, setPhone] = useState("");
  const [startedAt, setStartedAt] = useState(0);

  const start = useMutation({
    mutationFn: () => api<Payment>("/billing/checkout", { body: { product: product.id, provider: "trust", phone: phone.trim(), operator } }),
    onSuccess: () => setStartedAt(Date.now()),
  });
  const reference = start.data?.reference;
  const status = useQuery({
    queryKey: ["payment", reference],
    queryFn: () => api<Payment>(`/billing/payments/${reference}`),
    enabled: !!reference,
    refetchInterval: (q) => (q.state.data?.status === "pending" && Date.now() - startedAt < WAIT_MAX_MS ? POLL_MS : false),
  });
  const payment = status.data ?? start.data;
  const waiting = payment?.status === "pending";
  const timedOut = waiting && !status.isFetching && Date.now() - startedAt >= WAIT_MAX_MS;

  useEffect(() => {
    if (payment?.status === "paid") qc.invalidateQueries({ queryKey: ["me"] });
  }, [payment?.status, qc]);

  const phoneOk = phone.replace(/\D/g, "").length >= 8;
  const retry = () => { start.reset(); qc.removeQueries({ queryKey: ["payment", reference] }); };

  return (
    <Card featured className="mb-8">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="label-caps">Paiement mobile money</p>
          <h2 className="mt-1 font-display text-[24px] leading-[30px]">{product.label} · <span className="tabular">{fcfa(product.price)}</span></h2>
        </div>
        <button onClick={onClose} aria-label="Fermer le paiement" className="inline-flex size-11 items-center justify-center rounded-[4px] hover:bg-papier"><X size={20} strokeWidth={2} aria-hidden /></button>
      </div>

      {!payment && (
        <form className="mt-6 grid gap-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end" onSubmit={(e) => { e.preventDefault(); start.mutate(); }}>
          <Field label="Opérateur" htmlFor="operator">
            <select id="operator" required value={operator} onChange={(e) => setOperator(e.target.value)} disabled={operators.isLoading}
              className="h-12 w-full rounded-[4px] border-2 border-encre bg-blanc px-3 text-[16px] text-[#14110F]">
              <option value="">{operators.isLoading ? "Chargement…" : "Choisir"}</option>
              {operators.data?.map((o) => <option key={o.code} value={o.code}>{o.name}</option>)}
            </select>
          </Field>
          <Field label="Numéro de téléphone" htmlFor="phone">
            <Input id="phone" type="tel" inputMode="tel" autoComplete="tel" required value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="6 99 00 00 00" />
          </Field>
          <Button type="submit" variant="primary" disabled={start.isPending || !operator || !phoneOk}>{start.isPending ? "Envoi…" : "Payer"}</Button>
          <div className="sm:col-span-3"><ErrorNote error={operators.error ?? start.error} /></div>
        </form>
      )}

      {waiting && !timedOut && (
        <div role="status" className="trame mt-6 flex items-center gap-3 rounded-[4px] border-2 border-encre p-4">
          <span className="flex items-center gap-3 rounded-[4px] border-2 border-encre bg-bulle px-3 py-2 font-bold">
            <Loader size={20} strokeWidth={2} className="animate-spin" aria-hidden />Validez le paiement sur votre téléphone.
          </span>
        </div>
      )}
      {timedOut && (
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <p className="font-bold">Paiement toujours en attente.</p>
          <Button onClick={() => { setStartedAt(Date.now()); status.refetch(); }}>Vérifier à nouveau</Button>
        </div>
      )}
      {payment?.status === "paid" && (
        <p role="status" className="mt-6 flex items-center gap-2 rounded-[4px] border-2 border-succes bg-bulle p-3 font-bold text-succes">
          <Check size={20} strokeWidth={2} aria-hidden />Paiement reçu. Votre solde est à jour.
        </p>
      )}
      {payment?.status === "failed" && (
        <div className="mt-6 flex flex-col gap-3">
          <ErrorNote error={new Error(payment.error || "Le paiement n'a pas abouti.")} />
          <Button className="self-start" onClick={retry}>Réessayer</Button>
        </div>
      )}
    </Card>
  );
}

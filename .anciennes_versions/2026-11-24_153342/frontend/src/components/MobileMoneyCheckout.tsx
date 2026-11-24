import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";
import { Check, Loader, X } from "lucide-react";
import { api, type Payment } from "@/lib/api";
import { Button, Card, ErrorNote, Field, Input } from "@/components/ink";

const POLL_MS = 3000;
const WAIT_MAX_MS = 3 * 60 * 1000;
export const fcfa = (n: number) => `${n.toLocaleString("fr-FR")} FCFA`;

export type CheckoutProduct = { id: "creator" | "studio" | "pack" | "don"; label: string; price: number };
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

/** Paiement mobile money : opérateur et numéro, puis attente de la validation sur le téléphone. */
export function MobileMoneyCheckout({ product, onClose, paidMessage }: { product: CheckoutProduct; onClose: () => void; paidMessage?: ReactNode }) {
  const qc = useQueryClient();
  const operators = useQuery({ queryKey: ["operators"], queryFn: async () => readOperators(await api<unknown>("/billing/operators")), staleTime: 10 * 60 * 1000 });
  const [operator, setOperator] = useState("");
  const [phone, setPhone] = useState("");
  const [startedAt, setStartedAt] = useState(0);

  const start = useMutation({
    mutationFn: () => api<Payment>("/billing/checkout", {
      body: { product: product.id, provider: "trust", phone: phone.trim(), operator, ...(product.id === "don" ? { amount: product.price } : {}) },
    }),
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
          <Check size={20} strokeWidth={2} aria-hidden />{paidMessage ?? "Paiement reçu. Votre solde est à jour."}
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

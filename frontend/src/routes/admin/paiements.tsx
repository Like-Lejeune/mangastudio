import { createFileRoute, Link } from "@tanstack/react-router";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { dateTime, INTENT_LABEL, money, PRODUCT_LABEL, type AdminPayment, type Paged, type PaymentIntent } from "@/lib/admin";
import { ErrorNote, Pill } from "@/components/ink";
import { Pager, Section, selectCls, Table } from "@/components/admin";

export const Route = createFileRoute("/admin/paiements")({ component: PaymentsPage });

function PaymentsPage() {
  const [status, setStatus] = useState("");
  const [ipage, setIpage] = useState(1);
  const [ppage, setPpage] = useState(1);
  const intents = useQuery({
    queryKey: ["admin", "intents", status, ipage],
    queryFn: () => api<Paged<PaymentIntent>>(`/admin/payment-intents?${new URLSearchParams({ status, page: String(ipage) })}`),
    placeholderData: keepPreviousData, refetchInterval: 20_000,
  });
  const payments = useQuery({
    queryKey: ["admin", "payments", ppage],
    queryFn: () => api<Paged<AdminPayment>>(`/admin/payments?page=${ppage}`), placeholderData: keepPreviousData,
  });

  return (
    <>
      <Section className="mt-0" title="Demandes de paiement" aside={
        <div className="flex items-center gap-2">
          <label htmlFor="st" className="label-caps">État</label>
          <select id="st" className={selectCls} value={status} onChange={(e) => { setStatus(e.target.value); setIpage(1); }}>
            <option value="">Toutes</option><option value="pending">En attente</option><option value="paid">Payées</option><option value="failed">Échouées</option>
          </select>
        </div>}>
        <p className="mb-4 text-[14px] leading-5 text-encre-douce">
          Chaque demande mobile money passée par TrustChange. Une demande en attente depuis plus de 15 minutes est signalée : le client n'a sans doute pas validé sur son téléphone.
        </p>
        <ErrorNote error={intents.error} />
        {intents.data && <>
          <Table head={["Quand", "Client", "Produit", ["Montant", "right"], "Opérateur", "État", "Référence"]} empty={intents.data.items.length === 0} minWidth={900}>
            {intents.data.items.map((i) => (
              <tr key={i.reference}>
                <td className="tabular whitespace-nowrap">{dateTime(i.created_at)}</td>
                <td>{i.user_id ? <Link to="/admin/utilisateurs/$id" params={{ id: i.user_id }} className="break-all underline">{i.user_email}</Link> : "—"}</td>
                <td>{PRODUCT_LABEL[i.product] ?? i.product}</td>
                <td className="tabular text-right">{money(i.amount, i.currency)}</td>
                <td>{i.operator || "—"}</td>
                <td>
                  <Pill tone={i.status === "paid" ? "succes" : i.status === "failed" ? "alerte" : "soleil"}>{INTENT_LABEL[i.status]}</Pill>
                  {i.stale && <p className="mt-1 text-[13px] font-bold text-alerte">Bloquée depuis plus de 15 min</p>}
                  {i.error && <p className="mt-1 text-[13px] text-encre-douce">{i.error}</p>}
                </td>
                <td className="tabular break-all text-[12px]">{i.reference}{i.provider_ref && <><br />TrustChange : {i.provider_ref}</>}</td>
              </tr>
            ))}
          </Table>
          <Pager page={intents.data.page} pages={intents.data.pages} total={intents.data.total} onPage={setIpage} />
        </>}
      </Section>

      <Section title="Paiements encaissés">
        <ErrorNote error={payments.error} />
        {payments.data && <>
          <Table head={["Quand", "Client", "Produit", ["Montant", "right"], "Moyen", "Référence"]} empty={payments.data.items.length === 0}>
            {payments.data.items.map((p) => (
              <tr key={p.id}>
                <td className="tabular whitespace-nowrap">{dateTime(p.created_at)}</td>
                <td>{p.user_id ? <Link to="/admin/utilisateurs/$id" params={{ id: p.user_id }} className="break-all underline">{p.user_email}</Link> : "—"}</td>
                <td>{PRODUCT_LABEL[p.product] ?? p.product}</td>
                <td className="tabular text-right font-bold">{money(p.amount, p.currency)}</td>
                <td>{p.provider === "trust" ? "Mobile money" : p.provider === "stripe" ? "Carte" : p.provider}</td>
                <td className="tabular break-all text-[12px]">{p.external_ref}</td>
              </tr>
            ))}
          </Table>
          <Pager page={payments.data.page} pages={payments.data.pages} total={payments.data.total} onPage={setPpage} />
        </>}
      </Section>
    </>
  );
}

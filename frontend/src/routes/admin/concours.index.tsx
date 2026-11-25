import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { dateLongue, PHASE_TON, type Concours } from "@/lib/concours";
import { FormulaireConcours, type ConcoursIn } from "@/components/FormulaireConcours";
import { Button, Card, ErrorNote, Pill } from "@/components/ink";

export const Route = createFileRoute("/admin/concours/")({ component: AdminConcours });

function AdminConcours() {
  const qc = useQueryClient();
  const nav = useNavigate();
  const [nouveau, setNouveau] = useState(false);
  const { data, error } = useQuery({ queryKey: ["admin", "concours"], queryFn: () => api<{ items: Concours[] }>("/admin/contests") });
  const creer = useMutation({
    mutationFn: (c: ConcoursIn) => api<Concours>("/admin/contests", { body: c }),
    onSuccess: (c) => { qc.invalidateQueries({ queryKey: ["admin"] }); nav({ to: "/admin/concours/$id", params: { id: c.id } }); },
  });
  return (
    <>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-2xl text-[14px] leading-5 text-encre-douce">
          Créez un concours (brouillon tant qu'il n'est pas visible). Pendant le concours, notez chaque histoire sur 20 ;
          après la clôture, proclamez les résultats : le classement est figé et les lots sont crédités.
        </p>
        {!nouveau && <Button variant="primary" onClick={() => setNouveau(true)}>Nouveau concours</Button>}
      </div>
      {nouveau && (
        <Card className="mb-8">
          <h2 className="mb-4 font-display text-[24px] leading-[30px]">Nouveau concours</h2>
          <FormulaireConcours onSubmit={(c) => creer.mutate(c)} pending={creer.isPending} error={creer.error} submitLabel="Créer le concours" />
          <Button className="mt-3" onClick={() => setNouveau(false)}>Annuler</Button>
        </Card>
      )}
      <ErrorNote error={error} />
      {data?.items.length === 0 && !nouveau && <p className="text-encre-douce">Aucun concours pour l'instant.</p>}
      <ul className="grid gap-4">
        {data?.items.map((c) => (
          <li key={c.id}>
            <Link to="/admin/concours/$id" params={{ id: c.id }} className="flex flex-wrap items-center justify-between gap-3 rounded-[8px] border-2 border-encre bg-bulle p-4 shadow-ink hover:bg-papier">
              <span className="min-w-0">
                <b className="font-display text-[20px]">{c.title}</b>
                <span className="block text-[13px] text-encre-douce">du {dateLongue(c.starts_at)} au {dateLongue(c.ends_at)} · {c.entries} participant{c.entries > 1 ? "s" : ""}</span>
              </span>
              <span className="flex gap-2">{!c.visible && <Pill tone="alerte">Brouillon</Pill>}<Pill tone={PHASE_TON[c.phase]}>{c.phase_label}</Pill></span>
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}

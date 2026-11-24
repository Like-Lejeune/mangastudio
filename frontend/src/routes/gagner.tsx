import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { CalendarClock, Check, Copy, Gift, Users } from "lucide-react";
import { api } from "@/lib/api";
import { Button, Card, Container, ErrorNote, Onomatopee, PageTitle, Pill, RequireAuth } from "@/components/ink";

export const Route = createFileRoute("/gagner")({
  head: () => ({ meta: [{ title: "Gagner des crédits — MangaStudio" }] }),
  component: () => <RequireAuth><GagnerPage /></RequireAuth>,
});

type Gagner = {
  code: string; link: string;
  rewards: { invitee: number; referrer: number; purchase: number; max: number };
  referrals: { name: string; created_at: string | null; status: "pending" | "qualified" | "checking" | "cancelled"; rewarded: boolean; purchase_rewarded: boolean }[];
  earned: number; rewarded_count: number;
  missions: { id: string; label: string; credits: number; done: boolean }[];
  weekly_refill: { amount: number; next: string };
};

const ETAT = {
  pending: { texte: "Inscrit, pas encore d'épisode", ton: "bulle" },
  qualified: { texte: "1er épisode terminé", ton: "succes" },
  checking: { texte: "En vérification", ton: "soleil" },
  cancelled: { texte: "Non retenu", ton: "bulle" },
} as const;

function GagnerPage() {
  const { data: g, error, isLoading } = useQuery({ queryKey: ["gagner"], queryFn: () => api<Gagner>("/me/gagner") });
  const [copie, setCopie] = useState<string | null>(null);
  if (isLoading) return <Container><p className="text-encre-douce">Chargement…</p></Container>;
  if (error || !g) return <Container><ErrorNote error={error ?? new Error("Indisponible.")} /></Container>;

  const copier = async (texte: string, quoi: string) => {
    try { await navigator.clipboard.writeText(texte); setCopie(quoi); setTimeout(() => setCopie(null), 2500); } catch { /* refusé */ }
  };
  const message = `Je crée mes propres mangas avec MangaStudio : tu décris une idée, il dessine les pages. Inscris-toi avec mon lien, tu reçois ${g.rewards.invitee} crédits en plus : ${g.link}`;
  const lundi = new Date(g.weekly_refill.next).toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" });

  return (
    <Container className="max-w-[960px]">
      <PageTitle sub="Invitez vos amis, accomplissez les missions et revenez chaque semaine : vos crédits gratuits s'ajoutent à votre solde.">
        Gagner des crédits
      </PageTitle>

      <Card featured className="relative">
        <Onomatopee className="absolute -top-5 right-4">+{g.rewards.referrer}</Onomatopee>
        <h2 className="flex items-center gap-2 font-display text-[24px] leading-[30px]"><Users size={24} strokeWidth={2} aria-hidden />Invitez vos amis</h2>
        <ul className="mt-3 flex flex-col gap-1 leading-7">
          <li>Votre ami reçoit <b>{g.rewards.invitee} crédits</b> en plus à la confirmation de son adresse.</li>
          <li>Vous recevez <b>{g.rewards.referrer} crédits</b> quand il termine son premier épisode.</li>
          <li>Et <b>{g.rewards.purchase} crédits</b> de plus à son premier achat.</li>
        </ul>
        <div className="mt-5 grid gap-3 sm:grid-cols-[auto_1fr]">
          <div>
            <p className="label-caps mb-1">Votre code</p>
            <button onClick={() => copier(g.code, "code")} className="tabular flex min-h-12 items-center gap-2 rounded-[4px] border-2 border-encre bg-blanc px-4 text-[22px] font-bold tracking-[0.15em]">
              {g.code}{copie === "code" ? <Check size={18} strokeWidth={2} aria-label="copié" /> : <Copy size={18} strokeWidth={2} aria-hidden />}
            </button>
          </div>
          <div className="min-w-0">
            <p className="label-caps mb-1">Votre lien d'invitation</p>
            <div className="flex gap-2">
              <input readOnly value={g.link} aria-label="Lien d'invitation" onFocus={(e) => e.currentTarget.select()}
                className="tabular min-h-12 min-w-0 flex-1 rounded-[4px] border-2 border-encre bg-blanc px-3 text-[14px]" />
              <Button onClick={() => copier(g.link, "lien")}>{copie === "lien" ? "Copié" : "Copier"}</Button>
            </div>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <a href={`https://wa.me/?text=${encodeURIComponent(message)}`} target="_blank" rel="noreferrer"
            className="inline-flex min-h-11 items-center rounded-[4px] border-2 border-encre bg-[#25D366] px-4 font-bold text-encre">Inviter sur WhatsApp</a>
          <a href={`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(g.link)}`} target="_blank" rel="noreferrer"
            className="inline-flex min-h-11 items-center rounded-[4px] border-2 border-encre bg-[#1877F2] px-4 font-bold text-white">Facebook</a>
        </div>
        <p className="mt-4 text-[13px] leading-5 text-encre-douce">
          Vos chapitres partagés et vos PDF portent aussi votre code. Jusqu'à {g.rewards.max} amis récompensés. Les invitations suspectes (comptes en série, même connexion) sont vérifiées avant d'être récompensées.
        </p>
      </Card>

      <div className="mt-8 grid gap-6 md:grid-cols-2">
        <Card>
          <h2 className="font-display text-[22px] leading-[28px]">Vos amis invités</h2>
          <p className="mt-1 text-encre-douce">
            <span className="tabular font-bold text-encre">{g.earned}</span> crédits gagnés · <span className="tabular">{g.rewarded_count}</span> / {g.rewards.max} amis récompensés
          </p>
          {g.referrals.length === 0 ? (
            <p className="mt-4 text-encre-douce">Personne pour l'instant. Partagez votre lien !</p>
          ) : (
            <ul className="mt-4 flex flex-col divide-y divide-trait">
              {g.referrals.map((r, i) => (
                <li key={i} className="flex flex-wrap items-center justify-between gap-2 py-2">
                  <span className="font-bold">{r.name}</span>
                  <span className="flex gap-1"><Pill tone={ETAT[r.status].ton}>{ETAT[r.status].texte}</Pill>{r.purchase_rewarded && <Pill tone="succes">+{g.rewards.purchase} achat</Pill>}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <div className="flex flex-col gap-6">
          <Card>
            <h2 className="flex items-center gap-2 font-display text-[22px] leading-[28px]"><Gift size={22} strokeWidth={2} aria-hidden />Missions</h2>
            <ul className="mt-3 flex flex-col gap-2">
              {g.missions.map((m) => (
                <li key={m.id} className="flex items-center gap-3">
                  <span className={`flex size-7 shrink-0 items-center justify-center rounded-full border-2 border-encre ${m.done ? "bg-succes text-bulle" : "bg-bulle"}`}>
                    {m.done && <Check size={16} strokeWidth={3} aria-label="fait" />}
                  </span>
                  <span className={m.done ? "text-encre-douce line-through" : ""}>{m.label}</span>
                  <span className="tabular ml-auto font-bold">+{m.credits}</span>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-[13px] text-encre-douce">Partager : depuis un épisode terminé. Avis : <Link to="/mon-avis" className="underline">donner mon avis</Link>.</p>
          </Card>
          <Card>
            <h2 className="flex items-center gap-2 font-display text-[22px] leading-[28px]"><CalendarClock size={22} strokeWidth={2} aria-hidden />Recharge de la semaine</h2>
            <p className="mt-2 leading-7">
              Avec le plan gratuit, votre solde remonte à <b>{g.weekly_refill.amount} crédits</b> chaque semaine, à votre première visite. Prochaine recharge à partir du <b>{lundi}</b>.
            </p>
            <p className="mt-1 text-[13px] text-encre-douce">Elle ne s'additionne pas : si vous avez déjà {g.weekly_refill.amount} crédits ou plus, rien ne change.</p>
          </Card>
        </div>
      </div>
    </Container>
  );
}

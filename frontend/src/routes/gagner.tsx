import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { CalendarClock, Check, Copy, Gift, Users } from "lucide-react";
import { api } from "@/lib/api";
import { intlLocale, tr } from "@/lib/i18n";
import { Button, Card, Container, ErrorNote, Onomatopee, PageTitle, Pill, RequireAuth } from "@/components/ink";

export const Route = createFileRoute("/gagner")({
  head: () => ({ meta: [{ title: tr("Gagner des crédits — MangaStudio", "Earn credits — MangaStudio") }] }),
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

const etat = (s: "pending" | "qualified" | "checking" | "cancelled") => ({
  pending: { texte: tr("Inscrit, pas encore d'épisode", "Signed up, no episode yet"), ton: "bulle" },
  qualified: { texte: tr("1er épisode terminé", "1st episode done"), ton: "succes" },
  checking: { texte: tr("En vérification", "Being checked"), ton: "soleil" },
  cancelled: { texte: tr("Non retenu", "Not accepted"), ton: "bulle" },
} as const)[s];

const MISSION_EN: Record<string, string> = { first_episode: "Finish your first episode", first_share: "Share a chapter by link", testimonial: "Have a review published on the home page" };

function GagnerPage() {
  const { data: g, error, isLoading } = useQuery({ queryKey: ["gagner"], queryFn: () => api<Gagner>("/me/gagner") });
  const [copie, setCopie] = useState<string | null>(null);
  if (isLoading) return <Container><p className="text-encre-douce">{tr("Chargement…", "Loading…")}</p></Container>;
  if (error || !g) return <Container><ErrorNote error={error ?? new Error(tr("Indisponible.", "Unavailable."))} /></Container>;

  const copier = async (texte: string, quoi: string) => {
    try { await navigator.clipboard.writeText(texte); setCopie(quoi); setTimeout(() => setCopie(null), 2500); } catch { /* refusé */ }
  };
  const message = tr(
    `Je crée mes propres mangas avec MangaStudio : tu décris une idée, il dessine les pages. Inscris-toi avec mon lien, tu reçois ${g.rewards.invitee} crédits en plus : ${g.link}`,
    `I make my own manga with MangaStudio: you describe an idea, it draws the pages. Sign up with my link and get ${g.rewards.invitee} extra credits: ${g.link}`,
  );
  const lundi = new Date(g.weekly_refill.next).toLocaleDateString(intlLocale(), { weekday: "long", day: "numeric", month: "long" });

  return (
    <Container className="max-w-[960px]">
      <PageTitle sub={tr("Invitez vos amis, accomplissez les missions et revenez chaque semaine : vos crédits gratuits s'ajoutent à votre solde.", "Invite your friends, complete missions and come back every week: your free credits are added to your balance.")}>
        {tr("Gagner des crédits", "Earn credits")}
      </PageTitle>

      <Card featured className="relative">
        <Onomatopee className="absolute -top-5 right-4">+{g.rewards.referrer}</Onomatopee>
        <h2 className="flex items-center gap-2 font-display text-[24px] leading-[30px]"><Users size={24} strokeWidth={2} aria-hidden />{tr("Invitez vos amis", "Invite your friends")}</h2>
        <ul className="mt-3 flex flex-col gap-1 leading-7">
          <li>{tr("Votre ami reçoit ", "Your friend gets ")}<b>{g.rewards.invitee} {tr("crédits", "credits")}</b>{tr(" en plus à la confirmation de son adresse.", " extra when they confirm their email.")}</li>
          <li>{tr("Vous recevez ", "You get ")}<b>{g.rewards.referrer} {tr("crédits", "credits")}</b>{tr(" quand il termine son premier épisode.", " when they finish their first episode.")}</li>
          <li>{tr("Et ", "And ")}<b>{g.rewards.purchase} {tr("crédits", "credits")}</b>{tr(" de plus à son premier achat.", " more on their first purchase.")}</li>
        </ul>
        <div className="mt-5 grid gap-3 sm:grid-cols-[auto_1fr]">
          <div>
            <p className="label-caps mb-1">{tr("Votre code", "Your code")}</p>
            <button onClick={() => copier(g.code, "code")} className="tabular flex min-h-12 items-center gap-2 rounded-[4px] border-2 border-encre bg-blanc px-4 text-[22px] font-bold tracking-[0.15em]">
              {g.code}{copie === "code" ? <Check size={18} strokeWidth={2} aria-label={tr("copié", "copied")} /> : <Copy size={18} strokeWidth={2} aria-hidden />}
            </button>
          </div>
          <div className="min-w-0">
            <p className="label-caps mb-1">{tr("Votre lien d'invitation", "Your invite link")}</p>
            <div className="flex gap-2">
              <input readOnly value={g.link} aria-label={tr("Lien d'invitation", "Invite link")} onFocus={(e) => e.currentTarget.select()}
                className="tabular min-h-12 min-w-0 flex-1 rounded-[4px] border-2 border-encre bg-blanc px-3 text-[14px]" />
              <Button onClick={() => copier(g.link, "lien")}>{copie === "lien" ? tr("Copié", "Copied") : tr("Copier", "Copy")}</Button>
            </div>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <a href={`https://wa.me/?text=${encodeURIComponent(message)}`} target="_blank" rel="noreferrer"
            className="inline-flex min-h-11 items-center rounded-[4px] border-2 border-encre bg-[#25D366] px-4 font-bold text-encre">{tr("Inviter sur WhatsApp", "Invite on WhatsApp")}</a>
          <a href={`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(g.link)}`} target="_blank" rel="noreferrer"
            className="inline-flex min-h-11 items-center rounded-[4px] border-2 border-encre bg-[#1877F2] px-4 font-bold text-white">Facebook</a>
        </div>
        <p className="mt-4 text-[13px] leading-5 text-encre-douce">
          {tr(`Vos chapitres partagés et vos PDF portent aussi votre code. Jusqu'à ${g.rewards.max} amis récompensés. Les invitations suspectes (comptes en série, même connexion) sont vérifiées avant d'être récompensées.`,
            `Your shared chapters and PDFs also carry your code. Up to ${g.rewards.max} friends rewarded. Suspicious invitations (accounts in bulk, same connection) are checked before being rewarded.`)}
        </p>
      </Card>

      <div className="mt-8 grid gap-6 md:grid-cols-2">
        <Card>
          <h2 className="font-display text-[22px] leading-[28px]">{tr("Vos amis invités", "Friends you invited")}</h2>
          <p className="mt-1 text-encre-douce">
            <span className="tabular font-bold text-encre">{g.earned}</span>{tr(" crédits gagnés · ", " credits earned · ")}<span className="tabular">{g.rewarded_count}</span> / {g.rewards.max}{tr(" amis récompensés", " friends rewarded")}
          </p>
          {g.referrals.length === 0 ? (
            <p className="mt-4 text-encre-douce">{tr("Personne pour l'instant. Partagez votre lien !", "Nobody yet. Share your link!")}</p>
          ) : (
            <ul className="mt-4 flex flex-col divide-y divide-trait">
              {g.referrals.map((r, i) => (
                <li key={i} className="flex flex-wrap items-center justify-between gap-2 py-2">
                  <span className="font-bold">{r.name}</span>
                  <span className="flex gap-1"><Pill tone={etat(r.status).ton}>{etat(r.status).texte}</Pill>{r.purchase_rewarded && <Pill tone="succes">+{g.rewards.purchase} {tr("achat", "purchase")}</Pill>}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <div className="flex flex-col gap-6">
          <Card>
            <h2 className="flex items-center gap-2 font-display text-[22px] leading-[28px]"><Gift size={22} strokeWidth={2} aria-hidden />{tr("Missions", "Missions")}</h2>
            <ul className="mt-3 flex flex-col gap-2">
              {g.missions.map((m) => (
                <li key={m.id} className="flex items-center gap-3">
                  <span className={`flex size-7 shrink-0 items-center justify-center rounded-full border-2 border-encre ${m.done ? "bg-succes text-bulle" : "bg-bulle"}`}>
                    {m.done && <Check size={16} strokeWidth={3} aria-label={tr("fait", "done")} />}
                  </span>
                  <span className={m.done ? "text-encre-douce line-through" : ""}>{tr(m.label, MISSION_EN[m.id] ?? m.label)}</span>
                  <span className="tabular ml-auto font-bold">+{m.credits}</span>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-[13px] text-encre-douce">{tr("Partager : depuis un épisode terminé. Avis : ", "Share: from a finished episode. Review: ")}<Link to="/mon-avis" className="underline">{tr("donner mon avis", "leave a review")}</Link>.</p>
          </Card>
          <Card>
            <h2 className="flex items-center gap-2 font-display text-[22px] leading-[28px]"><CalendarClock size={22} strokeWidth={2} aria-hidden />{tr("Recharge de la semaine", "Weekly top-up")}</h2>
            <p className="mt-2 leading-7">
              {tr("Avec le plan gratuit, votre solde remonte à ", "On the free plan, your balance goes back up to ")}<b>{g.weekly_refill.amount} {tr("crédits", "credits")}</b>{tr(" chaque semaine, à votre première visite. Prochaine recharge à partir du ", " every week, on your first visit. Next top-up from ")}<b>{lundi}</b>.
            </p>
            <p className="mt-1 text-[13px] text-encre-douce">{tr(`Elle ne s'additionne pas : si vous avez déjà ${g.weekly_refill.amount} crédits ou plus, rien ne change.`, `It doesn't add up: if you already have ${g.weekly_refill.amount} credits or more, nothing changes.`)}</p>
          </Card>
        </div>
      </div>
    </Container>
  );
}

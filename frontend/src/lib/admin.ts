// Formes renvoyées par les routes /admin de l'API, et mise en forme commune aux écrans d'administration.

export type Paged<T> = { items: T[]; total: number; page: number; size: number; pages: number };

export type Daily = { date: string; signups: number; episodes: number; revenue_xaf: number; cost_usd: number };
export type Overview = {
  users: { total: number; suspended: number; new_7d: number; new_30d: number; paying: { creator: number; studio: number } };
  revenue: Record<string, { all: number; month: number; count: number }>;
  donations: { all: number; month: number; count: number };
  payments: { pending_30d: number; failed_30d: number; paid_30d: number };
  episodes: { total: number; running: number; by_status: Record<string, number> };
  credits: { debited: number; outstanding: number; images: number };
  ai: { cost_usd_all: number; cost_usd_30d: number; cost_per_credit_usd: number | null };
  moderation: { blocked_7d: number; flagged_7d: number };
  daily: Daily[];
  problems: { id: string; number: number; title: string; status: string; error: string; series_title: string; owner_email: string; created_at: string }[];
  moderation_events: ModerationEvent[];
  testimonials_pending: number;
  budget: { limit_usd: number; spent_today_usd: number; ratio: number | null };
  generated_at: string;
};

export type AdminUser = {
  id: string; email: string; display_name: string; is_admin: boolean; is_active: boolean; email_verified: boolean; plan: string; plan_name: string;
  credits: number; episodes: number; last_episode_at: string | null; created_at: string;
};
export type ModerationEvent = { id: string; checkpoint: string; action: string; rule: string; excerpt: string; user_email?: string | null; episode_id?: string | null; created_at: string };
export type AdminAction = { id: string; admin_email: string; action: string; target_type: string; target_id: string; detail: string; created_at: string };
export type AdminEpisode = {
  id: string; number: number; title: string; status: string; error: string; page_count: number; series_title: string;
  owner_email: string; owner_id: string; created_at: string; credits: number; cost_usd: number; images: number; tokens: number;
};
export type UserDetail = {
  id: string; email: string; display_name: string; is_admin: boolean; is_active: boolean; email_verified: boolean; created_at: string;
  plan: { id: string; name: string };
  subscription: { plan: string; status: string; provider: string; period_end: string } | null;
  credits: { total: number; monthly: number; pack: number };
  ledger: { id: string; delta: number; bucket: string; kind: string; episode_id: string | null; note: string; created_at: string }[];
  payments: AdminPayment[];
  payment_intents: PaymentIntent[];
  episodes: (Omit<AdminEpisode, "owner_email" | "owner_id" | "error" | "credits">)[];
  moderation_events: ModerationEvent[];
  admin_actions: AdminAction[];
};
export type AdminPayment = { id: string; user_id?: string; user_email?: string; provider: string; product: string; amount: number; currency: string; external_ref: string; created_at: string };
export type PaymentIntent = {
  reference: string; user_id?: string; user_email?: string; product: string; amount: number; currency: string; operator: string;
  provider_ref?: string | null; status: "pending" | "paid" | "failed"; error: string; stale?: boolean; created_at: string;
};

const nf = new Intl.NumberFormat("fr-FR");
export const num = (n: number | null | undefined) => nf.format(n ?? 0);
export const fcfa = (n: number) => `${nf.format(n)} FCFA`;
export const usd = (n: number, digits = 2) => `${n.toLocaleString("fr-FR", { minimumFractionDigits: digits, maximumFractionDigits: digits })} $`;
export const money = (amount: number, currency: string) => (currency === "XAF" ? fcfa(amount) : currency === "USD" ? usd(amount / 100) : `${nf.format(amount)} ${currency}`);
export const dateTime = (iso: string | null | undefined) =>
  iso ? new Date(iso).toLocaleString("fr-FR", { day: "2-digit", month: "2-digit", year: "2-digit", hour: "2-digit", minute: "2-digit" }) : "—";
export const day = (iso: string | null | undefined) => (iso ? new Date(iso).toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "numeric" }) : "—");

export const PRODUCT_LABEL: Record<string, string> = { creator: "Plan Créateur", studio: "Plan Studio", pack: "Pack de 50 crédits", pack15: "Pack de 15 crédits", pack25: "Pack de 25 crédits", don: "Don" };
export const PLAN_LABEL: Record<string, string> = { free: "Découverte", creator: "Créateur", studio: "Studio" };
export const KIND_LABEL: Record<string, string> = { grant: "Attribution", reserve: "Réserve", refund: "Remboursement", expire: "Retrait ou expiration" };
export const CHECKPOINT_LABEL: Record<string, string> = { input: "Saisie", script: "Scénario", image: "Image" };
export const ACTION_LABEL: Record<string, string> = {
  credits: "Crédits", plan: "Plan", suspend: "Suspension", reactivate: "Réactivation", role: "Rôle", term: "Mot bloqué", scene_rule: "Scène interdite", budget_alert: "Alerte budget IA", testimonial: "Avis", verify_email: "Adresse confirmée",
};
export const INTENT_LABEL: Record<string, string> = { pending: "En attente", paid: "Payé", failed: "Échoué" };

// Concours : formes renvoyées par l'API.
import type { CarteHistoire } from "@/lib/galerie";
import { getLang, intlLocale, tr } from "@/lib/i18n";

export type Phase = "a_venir" | "en_cours" | "deliberation" | "termine";
export type Lot = { rank: number; credits: number; studio_days: number; label: string };
export type Concours = {
  id: string; slug: string; title: string; theme: string; description: string; rules: string; style: string;
  new_only: boolean; max_entries: number; prizes: Lot[]; starts_at: string; ends_at: string; results_at: string | null;
  visible: boolean; phase: Phase; phase_label: string; entries: number;
  // administration seulement : version anglaise telle qu'enregistrée
  title_en?: string; theme_en?: string; description_en?: string; rules_en?: string;
};
export type Participation = CarteHistoire & {
  entry_id: string; contest_likes: number; rank: number | null; score: number | null; prize: string; jury_score: number | null;
  // administration seulement
  email?: string; user_id?: string; publication_status?: string; disqualified?: string; entered_at?: string;
};
export type ConcoursDetail = Concours & {
  entries_list: Participation[];
  mine?: { entry_id: string; publication_id: string; publication_status: string; disqualified: string }[];
  eligible?: { publication_id: string; title: string; status: string; ok: boolean; why: string | null }[];
};

export const PHASE_TON: Record<Phase, "succes" | "soleil" | "indigo" | "bulle"> = {
  en_cours: "succes", a_venir: "soleil", deliberation: "indigo", termine: "bulle",
};

export function rangLabel(r: number): string {
  if (getLang() === "en") {
    const suffix = r % 100 >= 10 && r % 100 <= 20 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" } as Record<number, string>)[r % 10] ?? "th";
    return `${r}${suffix} prize`;
  }
  return r === 1 ? "1er prix" : `${r}e prix`;
}

export const dateLongue = (iso: string) =>
  new Intl.DateTimeFormat(intlLocale(), { day: "numeric", month: "long", year: "numeric" }).format(new Date(iso));
export const dateHeure = (iso: string) =>
  new Intl.DateTimeFormat(intlLocale(), { day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" }).format(new Date(iso));

/** « dans 3 jours », « dans 5 h » : le temps qui reste avant une date. */
export function reste(iso: string): string {
  const ms = new Date(iso).getTime() - Date.now();
  if (ms <= 0) return tr("terminé", "ended");
  const h = Math.floor(ms / 3_600_000);
  if (h >= 48) return tr(`${Math.floor(h / 24)} jours`, `${Math.floor(h / 24)} days`);
  if (h >= 1) return `${h} h`;
  return `${Math.max(1, Math.floor(ms / 60_000))} min`;
}

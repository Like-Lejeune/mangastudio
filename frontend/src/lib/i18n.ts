/**
 * Français / anglais.
 *
 * Usage dans un composant :   const { t, lang, locale } = useT();   t("Bonjour", "Hello")
 * Hors composant :            tr("Bonjour", "Hello")   (lit la langue courante)
 *
 * La langue : choix mémorisé dans le navigateur, sinon celle du navigateur (français si elle commence
 * par « fr », anglais sinon). Le bouton FR / EN la change partout et l'enregistre dans le compte.
 * L'administration reste en français.
 */
import { useSyncExternalStore } from "react";

export type Lang = "fr" | "en";
const KEY = "mangastudio.lang";
const listeners = new Set<() => void>();

function detect(): Lang {
  if (typeof window === "undefined") return "fr";
  try {
    const saved = localStorage.getItem(KEY);
    if (saved === "fr" || saved === "en") return saved;
  } catch { /* stockage indisponible */ }
  const nav = (navigator.languages?.[0] ?? navigator.language ?? "fr").toLowerCase();
  return nav.startsWith("fr") ? "fr" : "en";
}

let current: Lang = detect();
if (typeof document !== "undefined") document.documentElement.lang = current;

export const getLang = (): Lang => current;

export function setLang(l: Lang, opts: { remember?: boolean } = { remember: true }): void {
  if (l === current) return;
  current = l;
  if (opts.remember !== false) {
    try { localStorage.setItem(KEY, l); } catch { /* stockage indisponible */ }
  }
  if (typeof document !== "undefined") document.documentElement.lang = l;
  listeners.forEach((fn) => fn());
}

/** Le compte a une langue enregistrée : elle s'applique, sauf si ce navigateur a déjà un choix explicite. */
export function adoptAccountLang(l: string | null | undefined): void {
  if (l !== "fr" && l !== "en") return;
  let saved: string | null = null;
  try { saved = localStorage.getItem(KEY); } catch { /* */ }
  if (!saved) setLang(l);
}

const subscribe = (fn: () => void) => { listeners.add(fn); return () => { listeners.delete(fn); }; };

export function useLang(): Lang {
  return useSyncExternalStore(subscribe, getLang, () => "fr");
}

export const tr = (fr: string, en: string): string => (current === "en" ? en : fr);

/** Locale Intl de la langue courante, pour les dates et les nombres. */
export const intlLocale = (l: Lang = current) => (l === "en" ? "en-GB" : "fr-FR");

export function useT() {
  const lang = useLang();
  return {
    lang,
    locale: intlLocale(lang),
    t: (fr: string, en: string) => (lang === "en" ? en : fr),
  };
}

/** Choisit la version d'un contenu bilingue : { fr, en }. */
export function pick<T>(v: { fr: T; en: T }, l: Lang = current): T {
  return l === "en" ? v.en : v.fr;
}
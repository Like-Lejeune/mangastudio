// Galerie publique « À lire » : formes renvoyées par l'API.
export type CarteHistoire = {
  id: string; series_title: string; number: number; title?: string | null; style?: string | null; author: string;
  cover_url?: string | null; pages: number; likes: number; liked: boolean; featured: boolean; published_at: string | null;
  likes_week?: number;
};
export type Histoire = CarteHistoire & { premise: string; page_urls: string[]; is_author: boolean };
export type PageGalerie = { items: CarteHistoire[]; total: number; page: number; size: number; pages: number };
export type TriGalerie = "recentes" | "populaires" | "semaine" | "coups";

/** Côté auteur : où en est la publication d'un épisode (null : jamais proposé). */
export type MaPublication = {
  id: string; status: "pending" | "published" | "rejected" | "withdrawn"; reason: string; likes: number; featured: boolean;
  requested_at: string | null; published_at: string | null;
} | null;

export const titreHistoire = (c: Pick<CarteHistoire, "series_title" | "number" | "title">) =>
  `${c.series_title} — ${c.title || `Épisode ${c.number}`}`;

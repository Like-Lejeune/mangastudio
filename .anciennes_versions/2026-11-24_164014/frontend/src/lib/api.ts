const TOKEN_KEY = "mangastudio.token";
const BASE = (import.meta.env['VITE_API_URL'] as string | undefined) ?? "http://localhost:8000";

const listeners = new Set<() => void>();
/** Téléchargement d'un fichier protégé (ex. PDF) : le jeton part dans l'en-tête, puis le navigateur enregistre. */
export async function downloadFile(path: string, filename: string): Promise<void> {
  const token = tokenStore.get();
  const r = await fetch(`${BASE}${path}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
  if (!r.ok) {
    let detail: unknown = null;
    try { detail = (await r.json()).detail; } catch { /* réponse non JSON */ }
    const d = detail as { message?: string; code?: string } | string | null;
    throw new ApiError(typeof d === "string" ? d : d?.message ?? "Téléchargement impossible.", r.status, typeof d === "object" && d ? d.code : undefined);
  }
  const url = URL.createObjectURL(await r.blob());
  const a = document.createElement("a");
  a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}

export const tokenStore = {
  get: () => (typeof window === "undefined" ? null : localStorage.getItem(TOKEN_KEY)),
  set(t: string | null) {
    if (t) localStorage.setItem(TOKEN_KEY, t);
    else localStorage.removeItem(TOKEN_KEY);
    listeners.forEach((l) => l());
  },
  subscribe(l: () => void) {
    listeners.add(l);
    return () => listeners.delete(l);
  },
};

export class ApiError extends Error {
  constructor(message: string, public status: number, public code?: string) {
    super(message);
  }
}

export async function api<T>(path: string, opts: { method?: string; body?: unknown } = {}): Promise<T> {
  const token = tokenStore.get();
  let res: Response;
  try {
    res = await fetch(BASE + path, {
      method: opts.method ?? (opts.body ? "POST" : "GET"),
      headers: {
        ...(opts.body ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: opts.body ? JSON.stringify(opts.body) : null,
    });
  } catch {
    throw new ApiError("Le studio est injoignable pour le moment. Réessayez dans un instant.", 0);
  }
  if (res.status === 401 && token) {
    tokenStore.set(null);
    if (!location.pathname.startsWith("/connexion")) location.href = "/connexion";
  }
  if (!res.ok) {
    let detail: unknown = null;
    try { detail = (await res.json()).detail; } catch { /* vide */ }
    if (detail && typeof detail === "object" && "message" in detail) {
      const d = detail as { code?: string; message: string };
      throw new ApiError(d.message, res.status, d.code);
    }
    // Erreur de validation de l'API : `detail` est une liste de champs refusés.
    if (Array.isArray(detail)) {
      const fields = detail.map((d) => String((d as { loc?: unknown[] }).loc?.at(-1) ?? "")).filter(Boolean);
      throw new ApiError(`Certains champs sont invalides${fields.length ? ` (${fields.join(", ")})` : ""}. Vérifiez le formulaire.`, res.status, "validation");
    }
    throw new ApiError(typeof detail === "string" ? detail : "Une erreur est survenue.", res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ─── Formes renvoyées par l'API MangaStudio ──────────────────────────────────
export type Plan = { id: string; name: string; max_characters: number; max_pages: number; color: boolean; redraw: boolean };
export type Me = {
  id: string; email: string; is_admin: boolean; email_verified: boolean;
  display_name: string; credits: number; plan: Plan;
  subscription?: { status: string; provider: string; period_end: string } | null;
};
/** `premise` est l'idée de départ saisie à la création (l'API ne renvoie pas de champ `pitch`). */
export type SeriesItem = { id: string; title: string; premise: string; cover_url?: string | null };
export type Character = { id: string; name: string; role: string; description: string; sheet_url?: string | null };
export type EpisodeItem = { id: string; number: number; title?: string | null; status: string; page_count: number };
export type SeriesDetail = SeriesItem & { style?: string; palette?: "bw" | "color"; language?: string; characters: Character[]; episodes: EpisodeItem[] };
export type Stage = { stage: string; calls: number; input_tokens: number; output_tokens: number; images: number };
export type Usage = { input_tokens: number; output_tokens: number; images: number; credits: number; stages: Stage[] };
export type PageItem = { id: string; number: number; status?: "pending" | "done" | "failed"; url?: string | null; attempts?: number; editor_note?: string };
export type Episode = EpisodeItem & { series_id?: string; error?: string | null; pages: PageItem[]; usage?: Usage | null; share_url?: string | null };

export type PlanOffer = Plan & { credits: number; price_usd_cents: number; price_xaf: number };
export type PackOffer = { id: "pack15" | "pack25" | "pack"; credits: number; price_usd_cents: number; price_xaf: number };
export type Plans = { plans: PlanOffer[]; pack: { credits: number; price_usd_cents: number; price_xaf: number }; packs?: PackOffer[] };
/** Demande de paiement mobile money : `pending` jusqu'à la validation sur le téléphone. */
export type Payment = { reference: string; product: string; amount: number; currency: string; status: "pending" | "paid" | "failed"; error?: string; message?: string };

export const ACTIVE = ["queued", "designing", "writing", "moderating", "drawing"];
export const STATUS_LABEL: Record<string, string> = {
  queued: "En attente", designing: "Design des personnages", writing: "Écriture du scénario",
  moderating: "Vérification du contenu", drawing: "Dessin des pages", done: "Terminé",
  blocked: "Refusé", failed: "Interrompu",
};

/** Réduit une photo à 1280 px et la convertit en JPEG : l'API n'accepte que JPEG, PNG ou WebP, 3 Mo au plus. */
export async function photoToDataUrl(file: File, max = 1280): Promise<string> {
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, max / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  canvas.getContext("2d")!.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL("image/jpeg", 0.85);
}

/** Code de parrainage reçu par lien (?ref=CODE), gardé 30 jours jusqu'à l'inscription. */
const CLE = "mangastudio.ref";
const DUREE = 30 * 24 * 3600 * 1000;

export function retenirCodeDepuisUrl(): void {
  try {
    const code = new URLSearchParams(window.location.search).get("ref");
    if (code && /^[A-Za-z0-9]{4,12}$/.test(code)) localStorage.setItem(CLE, JSON.stringify({ code: code.toUpperCase(), at: Date.now() }));
  } catch { /* stockage indisponible : le lien d'invitation marche quand même s'il mène à l'inscription */ }
}

export function codeRetenu(): string | null {
  try {
    const v = JSON.parse(localStorage.getItem(CLE) ?? "null") as { code: string; at: number } | null;
    if (!v || Date.now() - v.at > DUREE) return null;
    return v.code;
  } catch {
    return null;
  }
}

export function oublierCode(): void {
  try { localStorage.removeItem(CLE); } catch { /* rien */ }
}

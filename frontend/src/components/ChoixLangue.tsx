import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { setLang, useLang, type Lang } from "@/lib/i18n";
import { useToken } from "@/lib/session";
import { cn } from "@/lib/utils";

/** Bouton FR / EN : change la langue partout, la mémorise, et l'enregistre dans le compte (e-mails, prochaine connexion). */
export function ChoixLangue({ className = "" }: { className?: string }) {
  const lang = useLang();
  const token = useToken();
  const qc = useQueryClient();
  const choisir = (l: Lang) => {
    if (l === lang) return;
    setLang(l);
    qc.invalidateQueries();                       // les textes venus de l'API (concours, messages) se rechargent
    if (token) api("/me", { method: "PATCH", body: { locale: l } }).catch(() => { /* la langue reste changée sur cet appareil */ });
  };
  return (
    <div role="group" aria-label={lang === "en" ? "Language" : "Langue"} className={cn("inline-flex overflow-hidden rounded-[4px] border-2 border-encre", className)}>
      {(["fr", "en"] as const).map((l) => (
        <button key={l} type="button" lang={l} aria-pressed={lang === l} onClick={() => choisir(l)}
          aria-label={l === "fr" ? "Français" : "English"}
          className={cn("min-h-9 min-w-10 px-2 text-[13px] font-bold uppercase", lang === l ? "bg-encre text-bulle" : "bg-bulle hover:bg-soleil")}>
          {l}
        </button>
      ))}
    </div>
  );
}

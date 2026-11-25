import { useState } from "react";
import { cn } from "@/lib/utils";
import type { StyleManga } from "@/content/styles";

/** Image d'exemple d'un style ; trame et initiale tant que l'image n'a pas été générée. */
export function VignetteStyle({ style, className, legende = false }: { style: StyleManga; className?: string; legende?: boolean }) {
  const [absente, setAbsente] = useState(false);
  if (absente) {
    return (
      <div className={cn("trame flex items-center justify-center border-2 border-encre bg-bulle text-encre", className)} aria-hidden>
        {legende && <span className="rounded-[4px] border-2 border-encre bg-bulle px-3 py-1 text-center text-[14px] font-bold">{style.nom}<br /><span className="font-medium text-encre-douce">exemple à venir</span></span>}
      </div>
    );
  }
  return (
    <img src={`/styles/${style.id}.webp`} alt={`Exemple de page en style ${style.nom}`} loading="lazy" onError={() => setAbsente(true)}
      className={cn("border-2 border-encre bg-blanc object-cover object-top", className)} />
  );
}

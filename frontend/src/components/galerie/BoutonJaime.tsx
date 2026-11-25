import { Link } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Heart } from "lucide-react";
import { api } from "@/lib/api";
import { useToken } from "@/lib/session";
import { ErrorNote } from "@/components/ink";
import { cn } from "@/lib/utils";
import { tr } from "@/lib/i18n";

/** « J'aime » d'une histoire publiée. Sans compte : renvoie vers la connexion. */
export function BoutonJaime({ id, likes, liked, mine, grand }: { id: string; likes: number; liked: boolean; mine?: boolean; grand?: boolean }) {
  const token = useToken();
  const qc = useQueryClient();
  const m = useMutation({
    mutationFn: (aimer: boolean) => api<{ likes: number; liked: boolean }>(`/gallery/${id}/like`, { method: aimer ? "POST" : "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["galerie"] }),
  });
  const n = m.data?.likes ?? likes;
  const on = m.data?.liked ?? liked;
  const cls = cn("inline-flex items-center gap-2 rounded-[4px] border-2 border-encre font-bold", grand ? "min-h-12 px-5 text-[18px]" : "min-h-11 px-3",
    on ? "bg-vermillon text-sur-vermillon" : "bg-bulle hover:bg-soleil");
  const contenu = <><Heart size={grand ? 22 : 18} strokeWidth={2.5} aria-hidden className={on ? "fill-current" : ""} /><span className="tabular">{n}</span></>;

  if (!token || mine) {
    return mine
      ? <span className={cn(cls, "cursor-default bg-papier hover:bg-papier")} title={tr("Vos lecteurs peuvent aimer votre histoire", "Your readers can like your story")} aria-label={tr(`${n} j'aime`, `${n} likes`)}>{contenu}</span>
      : <Link to="/connexion" className={cls} aria-label={tr(`${n} j'aime. Connectez-vous pour aimer cette histoire`, `${n} likes. Sign in to like this story`)}>{contenu}</Link>;
  }
  return (
    <span className="inline-flex flex-col items-start gap-2">
      <button type="button" className={cls} aria-pressed={on} disabled={m.isPending} onClick={() => m.mutate(!on)}
        aria-label={on ? tr(`Vous aimez cette histoire (${n}). Retirer mon j'aime`, `You like this story (${n}). Remove my like`) : tr(`J'aime cette histoire (${n})`, `Like this story (${n})`)}>
        {contenu}
      </button>
      <ErrorNote error={m.error} inline />
    </span>
  );
}

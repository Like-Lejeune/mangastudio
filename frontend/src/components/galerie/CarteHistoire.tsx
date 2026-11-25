import { Link } from "@tanstack/react-router";
import { Heart, Sparkles } from "lucide-react";
import { styleParId } from "@/content/styles";
import { titreHistoire, type CarteHistoire as Carte } from "@/lib/galerie";
import { tr } from "@/lib/i18n";

/** Une histoire de la galerie : couverture, titre, auteur, « j'aime ». */
export function CarteHistoire({ c, semaine }: { c: Carte; semaine?: boolean }) {
  const style = c.style ? styleParId(c.style)?.nom : undefined;
  return (
    <Link to="/galerie/$id" params={{ id: c.id }}
      className="group flex h-full flex-col overflow-hidden rounded-[8px] border-2 border-encre bg-bulle shadow-ink transition-transform hover:-translate-y-1 focus-visible:-translate-y-1">
      <div className="relative aspect-[3/4] overflow-hidden border-b-2 border-encre bg-papier">
        {c.cover_url
          ? <img src={c.cover_url} alt="" loading="lazy" className="size-full object-cover transition-transform duration-500 group-hover:scale-[1.03]" />
          : <div className="trame size-full" aria-hidden />}
        {c.featured && (
          <span className="absolute left-2 top-2 inline-flex items-center gap-1 rounded-full border-2 border-encre bg-soleil px-2 py-0.5 text-[12px] font-bold text-encre">
            <Sparkles size={14} strokeWidth={2.5} aria-hidden />{tr("Coup de cœur", "Staff pick")}
          </span>
        )}
      </div>
      <div className="flex flex-1 flex-col p-4">
        <h3 className="font-display text-[20px] leading-[26px] group-hover:underline">{titreHistoire(c)}</h3>
        <p className="mt-1 text-[14px] text-encre-douce">{tr("par ", "by ")}<b className="text-encre">{c.author}</b>{style && <> · {style}</>} · {c.pages} pages</p>
        <p className="mt-auto flex items-center gap-1 pt-3 font-bold">
          <Heart size={16} strokeWidth={2.5} aria-hidden className={c.liked ? "fill-vermillon text-vermillon" : ""} />
          <span className="tabular">{c.likes}</span><span className="sr-only">{tr(" j'aime", " likes")}</span>
          {semaine && (c.likes_week ?? 0) > 0 && <span className="ml-2 text-[13px] font-medium text-encre-douce">+{c.likes_week} {tr("cette semaine", "this week")}</span>}
        </p>
      </div>
    </Link>
  );
}

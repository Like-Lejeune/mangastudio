import { Link, useNavigate } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { Heart, LogOut } from "lucide-react";
import { tokenStore } from "@/lib/api";
import { useMe, useToken } from "@/lib/session";
import { Pill } from "./ink";

export function TopBar() {
  const token = useToken();
  const { data: me } = useMe();
  const qc = useQueryClient();
  const nav = useNavigate();
  const navCls = "inline-flex min-h-11 items-center px-2 font-bold hover:underline";
  return (
    <header className="border-b-2 border-encre bg-bulle">
      <div className="mx-auto flex max-w-[1180px] flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 sm:px-6">
        <Link to="/" className="inline-flex min-h-11 items-center" aria-label="MangaStudio, accueil">
          <img src="/brand/logo.svg" alt="MangaStudio" className="h-9" />
        </Link>
        {token ? (
          <>
            <nav className="flex flex-wrap items-center gap-x-1" aria-label="Navigation principale">
              <Link to="/" className={navCls} activeProps={{ className: "text-vermillon" }} activeOptions={{ exact: true }}>Mes séries</Link>
              <Link to="/galerie" className={navCls} activeProps={{ className: "text-vermillon" }}>À lire</Link>
              <Link to="/concours" className={navCls} activeProps={{ className: "text-vermillon" }}>Concours</Link>
              <Link to="/abonnements" className={navCls} activeProps={{ className: "text-vermillon" }}>Abonnements</Link>
              <Link to="/faq" className={navCls} activeProps={{ className: "text-vermillon" }}>FAQ</Link>
              {me?.is_admin && <Link to="/admin" className={navCls} activeProps={{ className: "text-vermillon" }}>Administration</Link>}
            </nav>
            <div className="ml-auto flex items-center gap-2">
              <Link to="/soutenir" className="inline-flex min-h-11 items-center gap-1 rounded-[4px] px-2 font-bold text-vermillon hover:underline" aria-label="Nous soutenir">
                <Heart size={18} strokeWidth={2.5} aria-hidden /><span className="hidden sm:inline">Soutenir</span>
              </Link>
              {me && <Pill>Plan {me.plan.name}</Pill>}
              {me && (
                <Link to="/gagner" title="Gagner des crédits" className="rounded-full hover:ring-2 hover:ring-encre">
                  <Pill tone="soleil"><span className="tabular">{me.credits}</span> crédits <span aria-hidden>＋</span></Pill>
                </Link>
              )}
              <button
                className="inline-flex size-11 items-center justify-center rounded-[4px] hover:bg-papier"
                aria-label="Se déconnecter"
                onClick={async () => { await qc.cancelQueries(); qc.clear(); tokenStore.set(null); nav({ to: "/connexion", replace: true }); }}
              >
                <LogOut size={20} strokeWidth={2} aria-hidden />
              </button>
            </div>
          </>
        ) : token === null ? (
          <div className="ml-auto flex flex-wrap gap-2">
            <Link to="/galerie" className={navCls} activeProps={{ className: "text-vermillon" }}>À lire</Link>
            <Link to="/concours" className={navCls} activeProps={{ className: "text-vermillon" }}>Concours</Link>
            <Link to="/faq" className={navCls} activeProps={{ className: "text-vermillon" }}>FAQ</Link>
            <Link to="/soutenir" className={navCls} activeProps={{ className: "text-vermillon" }}>Nous soutenir</Link>
            <Link to="/connexion" className={navCls}>Connexion</Link>
          </div>
        ) : null}
      </div>
    </header>
  );
}

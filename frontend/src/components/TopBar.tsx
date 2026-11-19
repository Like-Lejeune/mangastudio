import { Link, useNavigate } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { LogOut } from "lucide-react";
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
            <nav className="flex items-center gap-1" aria-label="Navigation principale">
              <Link to="/" className={navCls} activeProps={{ className: "text-vermillon" }} activeOptions={{ exact: true }}>Mes séries</Link>
              <Link to="/abonnements" className={navCls} activeProps={{ className: "text-vermillon" }}>Abonnements</Link>
              {me?.is_admin && <Link to="/admin" className={navCls} activeProps={{ className: "text-vermillon" }}>Administration</Link>}
            </nav>
            <div className="ml-auto flex items-center gap-2">
              {me && <Pill>Plan {me.plan.name}</Pill>}
              {me && <Pill tone="soleil"><span className="tabular">{me.credits}</span> crédits</Pill>}
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
          <div className="ml-auto flex gap-2">
            <Link to="/connexion" className={navCls}>Connexion</Link>
          </div>
        ) : null}
      </div>
    </header>
  );
}

import { createFileRoute, Link, Outlet } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useMe } from "@/lib/session";
import { Container, RequireAuth } from "@/components/ink";

export const Route = createFileRoute("/admin")({
  head: () => ({ meta: [{ title: "Administration — MangaStudio" }, { name: "robots", content: "noindex" }] }),
  component: () => <RequireAuth><AdminLayout /></RequireAuth>,
});

const TABS = [
  ["/admin", "Vue d'ensemble", true],
  ["/admin/utilisateurs", "Utilisateurs", false],
  ["/admin/episodes", "Épisodes", false],
  ["/admin/paiements", "Paiements", false],
  ["/admin/avis", "Avis", false],
  ["/admin/parrainages", "Parrainages", false],
  ["/admin/moderation", "Modération", false],
  ["/admin/journal", "Journal", false],
] as const;

function AdminLayout() {
  const { data: me, isLoading } = useMe();
  const { data: aRelire } = useQuery({
    queryKey: ["admin", "avis", "compteur"], queryFn: () => api<{ total: number }>("/admin/testimonials?status=pending"),
    enabled: !!me?.is_admin, refetchInterval: 60_000,
  });
  const enAttente = aRelire?.total ?? 0;
  if (isLoading) return <Container><p className="text-encre-douce">Chargement…</p></Container>;
  if (!me?.is_admin) {
    return (
      <Container>
        <h1 className="font-display text-[32px] leading-[38px]">Accès réservé</h1>
        <p className="mt-2 text-encre-douce">Cet espace est réservé aux administrateurs.</p>
      </Container>
    );
  }
  return (
    <Container className="max-w-[1320px]">
      <div className="mb-6 flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="font-display text-[32px] leading-[38px] sm:text-[40px] sm:leading-[44px]">Administration</h1>
        <p className="text-[14px] text-encre-douce">Connecté en tant que {me.email}</p>
      </div>
      <nav aria-label="Rubriques d'administration" className="mb-8 flex flex-wrap gap-2 border-b-2 border-encre pb-3">
        {TABS.map(([to, label, exact]) => (
          <Link key={to} to={to} activeOptions={{ exact }}
            className="inline-flex min-h-11 items-center rounded-[4px] border-2 border-transparent px-3 font-bold hover:border-encre"
            activeProps={{ className: "!border-encre bg-encre text-bulle" }}>
            {label}
            {to === "/admin/avis" && enAttente > 0 && <span className="tabular ml-2 rounded-full bg-vermillon px-2 text-[12px] text-sur-vermillon" aria-label={`${enAttente} à relire`}>{enAttente}</span>}
          </Link>
        ))}
      </nav>
      <Outlet />
    </Container>
  );
}

import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Check, Pencil, Play, UserPlus } from "lucide-react";
import { api, photoToDataUrl, statusLabel, ACTIVE, type Character, type SeriesDetail } from "@/lib/api";
import { useMe } from "@/lib/session";
import { Button, Card, Container, ErrorNote, Field, Input, PageTitle, Pill, RequireAuth, Textarea } from "@/components/ink";
import { cn } from "@/lib/utils";
import { tr } from "@/lib/i18n";

export const Route = createFileRoute("/series/$id")({
  head: () => ({
    meta: [
      { title: tr("Série et nouvel épisode — MangaStudio", "Series and new episode — MangaStudio") },
      { name: "description", content: tr("Choisissez vos personnages et lancez un nouvel épisode de votre série.", "Choose your characters and start a new episode of your series.") },
      { property: "og:title", content: tr("Série — MangaStudio", "Series — MangaStudio") },
      { property: "og:description", content: tr("Choisissez vos personnages et lancez un nouvel épisode.", "Choose your characters and start a new episode.") },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: () => <RequireAuth><SeriesPage /></RequireAuth>,
});

function statusTone(s: string) {
  if (s === "done") return "succes" as const;
  if (s === "blocked" || s === "failed") return "alerte" as const;
  if (ACTIVE.includes(s)) return "indigo" as const;
  return "bulle" as const;
}

function SeriesPage() {
  const { id } = Route.useParams();
  const { data: s, isLoading, error } = useQuery({ queryKey: ["series", id], queryFn: () => api<SeriesDetail>(`/series/${id}`) });
  const { data: me } = useMe();
  const nav = useNavigate();
  const qc = useQueryClient();
  const [selected, setSelected] = useState<string[]>([]);
  const [pages, setPages] = useState(4);
  const [direction, setDirection] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const maxChars = me?.plan.max_characters ?? 1;
  const maxPages = Math.max(4, me?.plan.max_pages ?? 4);

  const launch = useMutation({
    mutationFn: () => api<{ id: string }>(`/series/${id}/episodes`, { body: { page_count: pages, character_ids: selected, direction } }),
    onSuccess: (e) => { qc.invalidateQueries({ queryKey: ["me"] }); qc.invalidateQueries({ queryKey: ["series", id] }); nav({ to: "/episodes/$id", params: { id: String(e.id) } }); },
  });

  if (isLoading) return <Container><p className="text-encre-douce">{tr("Chargement de la série…", "Loading the series…")}</p></Container>;
  if (error || !s) return <Container><ErrorNote error={error ?? new Error(tr("Série introuvable.", "Series not found."))} /></Container>;

  const chosen = s.characters.filter((c) => selected.includes(String(c.id)));
  const sheets = chosen.filter((c) => !c.sheet_url).length;
  const cover = s.cover_url ? 0 : 1;
  const total = pages + sheets + cover;
  const toggle = (cid: string) => setSelected((cur) => cur.includes(cid) ? cur.filter((x) => x !== cid) : cur.length >= maxChars ? cur : [...cur, cid]);
  const notEnough = me ? me.credits < total : false;

  return (
    <Container>
      <Link to="/" className="mb-4 inline-flex min-h-11 items-center font-bold text-indigo underline">{tr("Mes séries", "My series")}</Link>
      <PageTitle sub={s.premise}>{s.title}</PageTitle>
      <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
        <div className="flex flex-col gap-8">
          <section aria-labelledby="persos">
            <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
              <h2 id="persos" className="font-display text-[24px] leading-[30px]">{tr("Personnages", "Characters")}</h2>
              <p className="text-[14px] text-encre-douce"><span className="tabular">{selected.length}</span> / <span className="tabular">{maxChars}</span> {tr("sélectionnés", "selected")}</p>
            </div>
            {s.characters.length === 0 && <p className="mb-4 text-encre-douce">{tr("Ajoutez au moins un personnage pour lancer un épisode.", "Add at least one character to start an episode.")}</p>}
            <ul className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              {s.characters.map((c) => {
                const cid = String(c.id); const on = selected.includes(cid);
                const full = !on && selected.length >= maxChars;
                return (
                  <li key={cid} className="flex flex-col">
                    <label className={cn("relative flex flex-1 cursor-pointer flex-col rounded-[8px] border-2 border-encre bg-bulle p-3", on ? "shadow-ink-lg outline-3 outline-vermillon" : "shadow-ink", full && "cursor-not-allowed opacity-60")}>
                      <input type="checkbox" className="sr-only" checked={on} disabled={full} onChange={() => toggle(cid)} />
                      {c.sheet_url ? <img src={c.sheet_url} alt="" className="aspect-[3/2] w-full border-2 border-encre bg-blanc object-cover" /> : <div className="trame aspect-[3/2] w-full border-2 border-encre" aria-hidden />}
                      <span className="mt-2 font-bold">{c.name}</span>
                      <span className="text-[14px] leading-5 text-encre-douce">{c.role}</span>
                      {!c.sheet_url && <Pill tone="soleil" className="mt-2 self-start text-[12px]">{tr("Fiche à dessiner · 1 crédit", "Sheet to draw · 1 credit")}</Pill>}
                      <span className={cn("mt-2 inline-flex items-center gap-1 text-[13px] font-bold", on ? "text-vermillon" : "text-encre-douce")}>
                        {on ? <><Check size={16} strokeWidth={2} aria-hidden />{tr("Sélectionné", "Selected")}</> : tr("Non sélectionné", "Not selected")}
                      </span>
                    </label>
                    {!c.sheet_url && (
                      <button type="button" onClick={() => setEditing(cid)} className="mt-2 inline-flex min-h-11 items-center gap-1 text-[14px] font-bold text-indigo underline">
                        <Pencil size={14} strokeWidth={2.5} aria-hidden />{tr("Modifier", "Edit")} {c.name}
                      </button>
                    )}
                  </li>
                );
              })}
            </ul>
            {editing && s.characters.find((c) => String(c.id) === editing) && (
              <EditCharacter key={editing} seriesId={id} c={s.characters.find((c) => String(c.id) === editing)!} onClose={() => setEditing(null)} />
            )}
            <AddCharacter seriesId={id} />
          </section>

          <section aria-labelledby="eps">
            <h2 id="eps" className="mb-4 font-display text-[24px] leading-[30px]">{tr("Épisodes", "Episodes")}</h2>
            {s.episodes.length === 0 ? <p className="text-encre-douce">{tr("Aucun épisode pour l'instant.", "No episodes yet.")}</p> : (
              <ul className="flex flex-col gap-3">
                {s.episodes.map((e) => (
                  <li key={e.id}>
                    <Link to="/episodes/$id" params={{ id: String(e.id) }} className="flex min-h-14 flex-wrap items-center gap-3 rounded-[8px] border-2 border-encre bg-bulle px-4 py-2 shadow-ink hover:translate-x-[2px] hover:translate-y-[2px]">
                      <span className="tabular font-bold">n° {e.number}</span>
                      <span className="flex-1 font-bold">{e.title || tr(`Épisode ${e.number}`, `Episode ${e.number}`)}</span>
                      <span className="tabular text-[14px] text-encre-douce">{e.page_count} p.</span>
                      <Pill tone={statusTone(e.status)}>{statusLabel(e.status)}</Pill>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>

        <Card featured className="flex h-fit flex-col gap-6 lg:sticky lg:top-6">
          <h2 className="font-display text-[24px] leading-[30px]">{tr("Nouvel épisode", "New episode")}</h2>
          <Field label={tr("Nombre de pages", "Number of pages")} htmlFor="pages" hint={<p className="flex justify-between text-[12px] text-encre-douce"><span className="tabular">4</span><span className="tabular">{maxPages}</span></p>}>
            <div className="flex items-center gap-3">
              <input id="pages" type="range" min={4} max={maxPages} value={pages} onChange={(e) => setPages(+e.target.value)} className="h-11 flex-1 accent-vermillon" />
              <span className="tabular w-10 text-right text-[20px] font-bold">{pages}</span>
            </div>
          </Field>
          <Field label={tr("Orientation (facultatif)", "Direction (optional)")} htmlFor="dir">
            <Textarea id="dir" maxLength={800} value={direction} onChange={(e) => setDirection(e.target.value)} placeholder={tr("Ce que vous souhaitez voir dans cet épisode…", "What you'd like to see in this episode…")} />
          </Field>
          <div className="rounded-[8px] border-2 border-encre bg-papier p-4">
            <p className="label-caps mb-3">{tr("Réserve de crédits", "Credits reserved")}</p>
            <table className="w-full text-[14px] leading-5">
              <tbody>
                <tr><td className="py-1">{tr("Pages", "Pages")}</td><td className="tabular text-right">{pages}</td></tr>
                <tr><td className="py-1">{tr("Fiches à dessiner", "Sheets to draw")}</td><td className="tabular text-right">{sheets}</td></tr>
                <tr><td className="py-1">{tr("Couverture", "Cover")}</td><td className="tabular text-right">{cover}</td></tr>
                <tr className="border-t-2 border-encre font-bold"><td className="pt-2">Total</td><td className="tabular pt-2 text-right text-[18px]">{total}</td></tr>
              </tbody>
            </table>
            {me && <p className="mt-2 text-[13px] text-encre-douce">{tr("Solde : ", "Balance: ")}<span className="tabular">{me.credits}</span> {tr("crédits", "credits")}</p>}
            {notEnough && <p className="mt-2 text-[14px] font-bold text-alerte">{tr("Crédits insuffisants. ", "Not enough credits. ")}<Link to="/abonnements" className="text-indigo underline">{tr("Recharger", "Top up")}</Link></p>}
          </div>
          <ErrorNote error={launch.error} />
          <Button variant="primary" disabled={selected.length === 0 || launch.isPending} onClick={() => launch.mutate()}>
            <Play size={20} strokeWidth={2} aria-hidden />{launch.isPending ? tr("Lancement…", "Starting…") : tr("Lancer l'épisode", "Start the episode")}
          </Button>
          {selected.length === 0 && <p className="-mt-3 text-[13px] text-encre-douce">{tr("Cochez au moins un personnage.", "Select at least one character.")}</p>}
        </Card>
      </div>
      <SupprimerSerie s={s} />
    </Container>
  );
}

function AddCharacter({ seriesId }: { seriesId: string }) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState(""); const [role, setRole] = useState(""); const [description, setDescription] = useState("");
  const [photo, setPhoto] = useState<string | null>(null); const [consent, setConsent] = useState(false);
  const [photoError, setPhotoError] = useState(false);
  const qc = useQueryClient();
  const m = useMutation({
    mutationFn: () => api(`/series/${seriesId}/characters`, { body: { name, role, description, photo, consent: photo ? consent : false } }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["series", seriesId] }); setOpen(false); setName(""); setRole(""); setDescription(""); setPhoto(null); setConsent(false); },
  });
  const code = (m.error as { code?: string } | null)?.code;
  if (!open) return <Button className="mt-6" onClick={() => setOpen(true)}><UserPlus size={20} strokeWidth={2} aria-hidden />{tr("Ajouter un personnage", "Add a character")}</Button>;
  return (
    <Card className="mt-6">
      <h3 className="font-display text-[24px] leading-[30px]">{tr("Ajouter un personnage", "Add a character")}</h3>
      <form className="mt-4 grid gap-4 sm:grid-cols-2" onSubmit={(e) => { e.preventDefault(); m.mutate(); }}>
        <Field label={tr("Nom", "Name")} htmlFor="c-name"><Input id="c-name" required maxLength={60} value={name} onChange={(e) => setName(e.target.value)} /></Field>
        <Field label={tr("Rôle", "Role")} htmlFor="c-role"><Input id="c-role" maxLength={120} value={role} onChange={(e) => setRole(e.target.value)} placeholder={tr("Héroïne, mentor, rival…", "Heroine, mentor, rival…")} /></Field>
        <div className="sm:col-span-2"><Field label={tr("Description", "Description")} htmlFor="c-desc" hint={code === "blocked_terms" ? <ErrorNote inline error={m.error} /> : undefined}>
          <Textarea id="c-desc" maxLength={600} value={description} onChange={(e) => setDescription(e.target.value)} placeholder={tr("Apparence, tenue, caractère…", "Looks, outfit, personality…")} />
        </Field></div>
        <div className="sm:col-span-2"><Field label={tr("Photo (facultatif)", "Photo (optional)")} htmlFor="c-photo">
          <input id="c-photo" type="file" accept="image/jpeg,image/png,image/webp" className="min-h-11 text-[14px]" onChange={async (e) => {
            const f = e.target.files?.[0]; setPhotoError(false);
            if (!f) { setPhoto(null); return; }
            // Réduite avant l'envoi : une photo de téléphone dépasse la taille acceptée par l'API.
            try { setPhoto(await photoToDataUrl(f)); } catch { setPhoto(null); setPhotoError(true); }
          }} />
          {photoError && <p role="alert" className="text-[14px] font-medium text-alerte">{tr("Cette image est illisible. Choisissez un fichier JPEG, PNG ou WebP.", "This image can't be read. Choose a JPEG, PNG or WebP file.")}</p>}
        </Field></div>
        {photo && (
          <label className="flex min-h-11 items-start gap-3 sm:col-span-2">
            <input type="checkbox" required checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-1 size-5 accent-vermillon" />
            <span>{tr("J'ai l'accord de la personne sur cette photo", "I have the consent of the person in this photo")}</span>
          </label>
        )}
        {code !== "blocked_terms" && <div className="sm:col-span-2"><ErrorNote error={m.error} /></div>}
        <div className="flex flex-wrap gap-3 sm:col-span-2">
          <Button type="submit" disabled={m.isPending || (!!photo && !consent)}>{m.isPending ? tr("Ajout…", "Adding…") : tr("Ajouter", "Add")}</Button>
          <Button type="button" onClick={() => setOpen(false)}>{tr("Annuler", "Cancel")}</Button>
        </div>
      </form>
    </Card>
  );
}

/** Modifier un personnage pas encore dessiné : après un refus du dessinateur, on change son nom ou son apparence. */
function EditCharacter({ seriesId, c, onClose }: { seriesId: string; c: Character; onClose: () => void }) {
  const [name, setName] = useState(c.name); const [role, setRole] = useState(c.role); const [description, setDescription] = useState(c.description);
  const qc = useQueryClient();
  const m = useMutation({
    mutationFn: () => api(`/characters/${c.id}`, { method: "PATCH", body: { name, role, description } }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["series", seriesId] }); onClose(); },
  });
  return (
    <Card className="mt-6">
      <h3 className="font-display text-[24px] leading-[30px]">{tr("Modifier", "Edit")} {c.name}</h3>
      <p className="mt-1 text-[14px] leading-5 text-encre-douce">
        {tr("Inventez un personnage à vous : un nom et une apparence qui ne copient pas un héros connu (le dessinateur IA refuse les personnages protégés).", "Invent your own character: a name and a look that don't copy a well-known hero (the AI artist refuses copyrighted characters).")}
      </p>
      <form className="mt-4 grid gap-4 sm:grid-cols-2" onSubmit={(e) => { e.preventDefault(); m.mutate(); }}>
        <Field label={tr("Nom", "Name")} htmlFor="e-name"><Input id="e-name" required maxLength={60} value={name} onChange={(e) => setName(e.target.value)} /></Field>
        <Field label={tr("Rôle", "Role")} htmlFor="e-role"><Input id="e-role" maxLength={120} value={role} onChange={(e) => setRole(e.target.value)} /></Field>
        <div className="sm:col-span-2"><Field label="Description" htmlFor="e-desc">
          <Textarea id="e-desc" maxLength={600} value={description} onChange={(e) => setDescription(e.target.value)} placeholder={tr("Apparence, tenue, caractère…", "Looks, outfit, personality…")} />
        </Field></div>
        <div className="sm:col-span-2"><ErrorNote error={m.error} /></div>
        <div className="flex flex-wrap gap-3 sm:col-span-2">
          <Button type="submit" variant="primary" disabled={m.isPending}>{m.isPending ? tr("Enregistrement…", "Saving…") : tr("Enregistrer", "Save")}</Button>
          <Button type="button" onClick={onClose}>{tr("Annuler", "Cancel")}</Button>
        </div>
      </form>
    </Card>
  );
}

/** Supprimer toute l'histoire, définitivement. On fait taper « SUPPRIMER » pour éviter l'accident. */
function SupprimerSerie({ s }: { s: SeriesDetail }) {
  const [ouvert, setOuvert] = useState(false);
  const [mot, setMot] = useState("");
  const qc = useQueryClient();
  const nav = useNavigate();
  const m = useMutation({
    mutationFn: () => api(`/series/${s.id}`, { method: "DELETE" }),
    onSuccess: () => { qc.removeQueries({ queryKey: ["series", String(s.id)] }); qc.invalidateQueries({ queryKey: ["series"] }); nav({ to: "/" }); },
  });
  const enCours = s.episodes.some((e) => ACTIVE.includes(e.status));
  const n = s.episodes.length;
  return (
    <section className="mt-16 border-t-2 border-encre pt-8" aria-labelledby="danger">
      <h2 id="danger" className="font-display text-[22px] leading-[28px]">{tr("Supprimer cette histoire", "Delete this story")}</h2>
      {!ouvert ? (
        <>
          <p className="mt-2 max-w-2xl text-encre-douce">{tr("Efface la série, ses personnages et tous ses épisodes, pour de bon.", "Erases the series, its characters and all its episodes, for good.")}</p>
          <Button className="mt-4" onClick={() => setOuvert(true)} disabled={enCours}>{tr("Supprimer l'histoire…", "Delete the story…")}</Button>
          {enCours && <p className="mt-2 text-[13px] text-encre-douce">{tr("Impossible pendant qu'un épisode est en cours de création.", "Not possible while an episode is being created.")}</p>}
        </>
      ) : (
        <form className="mt-4 max-w-2xl rounded-[4px] border-2 border-alerte bg-bulle p-5" onSubmit={(e) => { e.preventDefault(); m.mutate(); }}>
          <p className="font-bold text-alerte">{tr("Cette action est irréversible.", "This can't be undone.")}</p>
          <ul className="mt-2 list-disc space-y-1 pl-6">
            <li>{tr(`${s.characters.length} personnage${s.characters.length > 1 ? "s" : ""} et ${n} épisode${n > 1 ? "s" : ""} seront effacés, avec toutes leurs pages.`,
              `${s.characters.length} character${s.characters.length === 1 ? "" : "s"} and ${n} episode${n === 1 ? "" : "s"} will be erased, with all their pages.`)}</li>
            <li>{tr("Les chapitres publiés disparaissent de la galerie, avec leurs « j'aime », et les liens de partage ne marcheront plus.", "Published chapters disappear from the gallery, with their likes, and share links will stop working.")}</li>
            <li>{tr("Les crédits déjà utilisés ne sont pas rendus ; ceux encore réservés le sont.", "Credits already used are not refunded; credits still reserved are.")}</li>
          </ul>
          <div className="mt-5">
            <Field label={tr("Pour confirmer, tapez SUPPRIMER", "To confirm, type DELETE")} htmlFor="confirm-del">
              <Input id="confirm-del" autoComplete="off" value={mot} onChange={(e) => setMot(e.target.value)} />
            </Field>
          </div>
          <ErrorNote error={m.error} />
          <div className="mt-4 flex flex-wrap gap-3">
            <Button type="submit" variant="primary" disabled={mot.trim().toUpperCase() !== tr("SUPPRIMER", "DELETE") || m.isPending}>
              {m.isPending ? tr("Suppression…", "Deleting…") : tr("Supprimer définitivement", "Delete permanently")}
            </Button>
            <Button type="button" onClick={() => { setOuvert(false); setMot(""); }}>{tr("Annuler", "Cancel")}</Button>
          </div>
        </form>
      )}
    </section>
  );
}

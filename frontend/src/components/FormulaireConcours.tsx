import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { CONTES_AFRIQUE, REGLEMENT_TYPE, REGLEMENT_TYPE_EN } from "@/content/concours";
import { STYLES_MANGA } from "@/content/styles";
import type { Concours } from "@/lib/concours";
import { Button, ErrorNote, Field, Input, Textarea } from "@/components/ink";

type Lot = { rank: number; credits: number; studio_days: number };
export type ConcoursIn = {
  title: string; slug: string; theme: string; description: string; rules: string;
  title_en: string; theme_en: string; description_en: string; rules_en: string; style: string; new_only: boolean;
  max_entries: number; prizes: Lot[]; starts_at: string; ends_at: string; visible: boolean;
};

/** ISO → valeur d'un champ datetime-local (heure locale du navigateur), et l'inverse. */
const versChamp = (iso: string) => { const d = new Date(iso); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0, 16); };
const versIso = (v: string) => new Date(v).toISOString();

const VIDE = { title: "", slug: "", theme: "", description: "", rules: REGLEMENT_TYPE,
  title_en: "", theme_en: "", description_en: "", rules_en: REGLEMENT_TYPE_EN, style: "", new_only: true, max_entries: 1,
  prizes: [{ rank: 1, credits: 100, studio_days: 0 }], starts: "", ends: "", visible: false };

export function FormulaireConcours({ initial, onSubmit, pending, error, submitLabel }: {
  initial?: Concours; onSubmit: (c: ConcoursIn) => void; pending: boolean; error: unknown; submitLabel: string;
}) {
  const [f, setF] = useState(() => initial ? {
    title: initial.title, slug: initial.slug, theme: initial.theme, description: initial.description, rules: initial.rules,
    title_en: initial.title_en ?? "", theme_en: initial.theme_en ?? "", description_en: initial.description_en ?? "", rules_en: initial.rules_en ?? "",
    style: initial.style, new_only: initial.new_only, max_entries: initial.max_entries,
    prizes: initial.prizes.map(({ rank, credits, studio_days }) => ({ rank, credits, studio_days })),
    starts: versChamp(initial.starts_at), ends: versChamp(initial.ends_at), visible: initial.visible,
  } : VIDE);
  const set = <K extends keyof typeof f>(k: K, v: (typeof f)[K]) => setF((x) => ({ ...x, [k]: v }));
  const setLot = (i: number, k: keyof Lot, v: number) => set("prizes", f.prizes.map((p, j) => (j === i ? { ...p, [k]: v } : p)));

  return (
    <form className="grid gap-5" onSubmit={(e) => {
      e.preventDefault();
      const { starts, ends, ...rest } = f;
      onSubmit({ ...rest, starts_at: versIso(starts), ends_at: versIso(ends) });
    }}>
      {!initial && (
        <p className="text-[14px]">
          <button type="button" className="min-h-11 font-bold text-indigo underline"
            onClick={() => setF({ ...VIDE, ...CONTES_AFRIQUE, slug: "", starts: CONTES_AFRIQUE.starts, ends: CONTES_AFRIQUE.ends })}>
            Préremplir avec « Contes et légendes d'Afrique » (21/12 → 17/01)
          </button>
        </p>
      )}
      <div className="grid gap-5 sm:grid-cols-2">
        <Field label="Titre" htmlFor="c-title"><Input id="c-title" required minLength={3} maxLength={120} value={f.title} onChange={(e) => set("title", e.target.value)} /></Field>
        <Field label="Adresse (facultatif)" htmlFor="c-slug" hint="Laissez vide : elle est tirée du titre.">
          <Input id="c-slug" maxLength={80} value={f.slug} onChange={(e) => set("slug", e.target.value)} placeholder="contes-et-legendes-d-afrique" />
        </Field>
      </div>
      <Field label="Thème, en une phrase" htmlFor="c-theme"><Input id="c-theme" maxLength={300} value={f.theme} onChange={(e) => set("theme", e.target.value)} /></Field>
      <Field label="Présentation" htmlFor="c-desc"><Textarea id="c-desc" maxLength={4000} value={f.description} onChange={(e) => set("description", e.target.value)} /></Field>
      <div className="grid gap-5 sm:grid-cols-2">
        <Field label="Ouverture" htmlFor="c-start"><Input id="c-start" type="datetime-local" required value={f.starts} onChange={(e) => set("starts", e.target.value)} /></Field>
        <Field label="Clôture" htmlFor="c-end"><Input id="c-end" type="datetime-local" required value={f.ends} onChange={(e) => set("ends", e.target.value)} /></Field>
      </div>
      <div className="grid gap-5 sm:grid-cols-2">
        <Field label="Style imposé" htmlFor="c-style">
          <select id="c-style" className="h-12 rounded-[4px] border-2 border-encre bg-bulle px-3" value={f.style} onChange={(e) => set("style", e.target.value)}>
            <option value="">Tous les styles</option>
            {STYLES_MANGA.map((s) => <option key={s.id} value={s.id}>{s.nom}</option>)}
          </select>
        </Field>
        <Field label="Histoires par participant" htmlFor="c-max">
          <Input id="c-max" type="number" min={1} max={10} value={f.max_entries} onChange={(e) => set("max_entries", Number(e.target.value))} />
        </Field>
      </div>
      <label className="flex cursor-pointer items-start gap-3">
        <input type="checkbox" className="mt-1 size-5" checked={f.new_only} onChange={(e) => set("new_only", e.target.checked)} />
        <span>Seulement les chapitres créés pendant le concours <span className="text-encre-douce">(recommandé : à armes égales)</span></span>
      </label>

      <fieldset className="rounded-[4px] border-2 border-encre p-4">
        <legend className="px-1 font-bold">Lots</legend>
        <p className="text-[13px] text-encre-douce">Crédités automatiquement à la proclamation. Les crédits ne périment pas ; les jours de plan Studio s'ajoutent à l'abonnement en cours.</p>
        <ul className="mt-3 flex flex-col gap-3">
          {f.prizes.map((p, i) => (
            <li key={i} className="flex flex-wrap items-end gap-3">
              <Field label="Rang" htmlFor={`l-r${i}`}><Input id={`l-r${i}`} type="number" min={1} max={20} className="w-20" value={p.rank} onChange={(e) => setLot(i, "rank", Number(e.target.value))} /></Field>
              <Field label="Crédits" htmlFor={`l-c${i}`}><Input id={`l-c${i}`} type="number" min={0} max={5000} className="w-28" value={p.credits} onChange={(e) => setLot(i, "credits", Number(e.target.value))} /></Field>
              <Field label="Jours Studio" htmlFor={`l-s${i}`}><Input id={`l-s${i}`} type="number" min={0} max={365} className="w-28" value={p.studio_days} onChange={(e) => setLot(i, "studio_days", Number(e.target.value))} /></Field>
              <button type="button" aria-label={`Supprimer le lot ${p.rank}`} className="inline-flex size-12 items-center justify-center rounded-[4px] border-2 border-encre bg-bulle hover:bg-papier"
                onClick={() => set("prizes", f.prizes.filter((_, j) => j !== i))}><Trash2 size={18} strokeWidth={2} aria-hidden /></button>
            </li>
          ))}
        </ul>
        <Button type="button" className="mt-3" onClick={() => set("prizes", [...f.prizes, { rank: f.prizes.length + 1, credits: 0, studio_days: 0 }])}>
          <Plus size={18} strokeWidth={2} aria-hidden />Ajouter un lot
        </Button>
      </fieldset>

      <Field label="Règlement" htmlFor="c-rules" hint="Règlement type prérempli : à faire valider, puis à adapter (dates, lots, jury).">
        <Textarea id="c-rules" className="min-h-72 font-mono text-[13px]" maxLength={20000} value={f.rules} onChange={(e) => set("rules", e.target.value)} />
      </Field>
      <details className="rounded-[4px] border-2 border-encre p-4" open={!!(f.title_en || f.theme_en || f.description_en)}>
        <summary className="min-h-11 cursor-pointer font-bold">Version anglaise (facultatif)</summary>
        <p className="mt-1 text-[13px] text-encre-douce">Montrée aux visiteurs qui ont choisi l'anglais. Un champ laissé vide affiche la version française.</p>
        <div className="mt-4 grid gap-5">
          <Field label="Title" htmlFor="c-title-en"><Input id="c-title-en" lang="en" maxLength={120} value={f.title_en} onChange={(e) => set("title_en", e.target.value)} /></Field>
          <Field label="Theme, in one sentence" htmlFor="c-theme-en"><Input id="c-theme-en" lang="en" maxLength={300} value={f.theme_en} onChange={(e) => set("theme_en", e.target.value)} /></Field>
          <Field label="Description" htmlFor="c-desc-en"><Textarea id="c-desc-en" lang="en" maxLength={4000} value={f.description_en} onChange={(e) => set("description_en", e.target.value)} /></Field>
          <Field label="Rules" htmlFor="c-rules-en"><Textarea id="c-rules-en" lang="en" className="min-h-72 font-mono text-[13px]" maxLength={20000} value={f.rules_en} onChange={(e) => set("rules_en", e.target.value)} /></Field>
        </div>
      </details>
      <label className="flex cursor-pointer items-start gap-3 rounded-[4px] border-2 border-encre bg-soleil p-3">
        <input type="checkbox" className="mt-1 size-5" checked={f.visible} onChange={(e) => set("visible", e.target.checked)} />
        <span><b>Visible du public.</b> Décoché : brouillon, seule l'administration le voit.</span>
      </label>
      <ErrorNote error={error} />
      <div><Button type="submit" variant="primary" disabled={pending}>{pending ? "Enregistrement…" : submitLabel}</Button></div>
    </form>
  );
}

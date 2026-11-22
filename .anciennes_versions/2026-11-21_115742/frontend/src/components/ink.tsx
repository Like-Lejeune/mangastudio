import { Link } from "@tanstack/react-router";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { ApiError } from "@/lib/api";

const btnBase =
  "inline-flex min-h-12 items-center justify-center gap-2 rounded-[4px] border-2 border-encre px-5 font-bold shadow-ink transition-[transform,box-shadow] duration-100 hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-ink-sm active:translate-x-[4px] active:translate-y-[4px] active:shadow-none disabled:pointer-events-none disabled:opacity-50";
export const btnClass = (v: "primary" | "secondary" = "secondary") =>
  cn(btnBase, v === "primary" ? "bg-vermillon text-sur-vermillon" : "bg-bulle text-encre");

export function Button({ variant = "secondary", className, ...p }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" }) {
  return <button {...p} className={cn(btnClass(variant), className)} />;
}

export function Card({ className, featured, children }: { className?: string; featured?: boolean; children: ReactNode }) {
  return <div className={cn("rounded-[8px] border-2 border-encre bg-bulle p-6", featured ? "shadow-ink-lg" : "shadow-ink", className)}>{children}</div>;
}

const fieldCls = "w-full rounded-[4px] border-2 border-encre bg-blanc px-3 text-[16px] text-[#14110F]";
export function Input(p: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...p} className={cn(fieldCls, "h-12", p.className)} />;
}
export function Textarea(p: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...p} className={cn(fieldCls, "min-h-28 py-2", p.className)} />;
}
export function Field({ label, htmlFor, children, hint }: { label: string; htmlFor: string; children: ReactNode; hint?: ReactNode }) {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={htmlFor} className="label-caps">{label}</label>
      {children}
      {hint}
    </div>
  );
}

export function Pill({ children, tone = "bulle", className }: { children: ReactNode; tone?: "bulle" | "soleil" | "succes" | "alerte" | "indigo"; className?: string }) {
  const tones = {
    bulle: "bg-bulle text-encre",
    soleil: "bg-soleil text-sur-soleil",
    succes: "bg-bulle text-succes",
    alerte: "bg-bulle text-alerte",
    indigo: "bg-bulle text-indigo",
  };
  return <span className={cn("inline-flex h-7 items-center gap-1 whitespace-nowrap rounded-full border-2 border-encre px-3 text-[13px] font-bold leading-none", tones[tone], className)}>{children}</span>;
}

export function Onomatopee({ children, className }: { children: ReactNode; className?: string }) {
  return <span aria-hidden className={cn("inline-block -rotate-6 border-2 border-encre bg-soleil px-3 py-1 font-bangers text-3xl tracking-wide text-sur-soleil shadow-ink", className)}>{children}</span>;
}

export function ErrorNote({ error, inline }: { error: unknown; inline?: boolean }) {
  if (!error) return null;
  const e = error as ApiError;
  const msg = e?.message ?? "Une erreur est survenue.";
  const toPlans = e?.code === "plan_limit" || e?.code === "insufficient_credits";
  return (
    <p role="alert" className={cn("text-[14px] leading-5 font-medium text-alerte", !inline && "rounded-[4px] border-2 border-alerte bg-bulle p-3")}>
      <span className="font-bold">Erreur : </span>{msg}
      {toPlans && (<> {" "}<Link to="/abonnements" className="font-bold text-indigo underline">Voir les abonnements</Link></>)}
    </p>
  );
}

export function PageTitle({ children, sub }: { children: ReactNode; sub?: ReactNode }) {
  return (
    <div className="mb-8">
      <h1 className="font-display text-[32px] leading-[38px] sm:text-[40px] sm:leading-[44px]">{children}</h1>
      {sub && <p className="mt-2 text-encre-douce">{sub}</p>}
    </div>
  );
}

export function Container({ children, className }: { children: ReactNode; className?: string }) {
  return <main className={cn("mx-auto w-full max-w-[1180px] px-4 py-8 sm:px-6 sm:py-12", className)}>{children}</main>;
}

import { Navigate } from "@tanstack/react-router";
import { useToken } from "@/lib/session";
export function RequireAuth({ children }: { children: ReactNode }) {
  const token = useToken();
  if (token === undefined) return null;
  if (!token) return <Navigate to="/connexion" replace />;
  return <>{children}</>;
}

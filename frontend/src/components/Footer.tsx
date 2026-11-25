import { Link } from "@tanstack/react-router";
import { Mail, Phone } from "lucide-react";
import { CONTACT } from "@/content/contact";
import { telHref } from "@/lib/contact";
import { useT } from "@/lib/i18n";

/** Pied de page commun à toutes les pages : liens d'aide et coordonnées. */
export function Footer() {
  const { t } = useT();
  const lien = "inline-flex min-h-9 items-center hover:text-encre hover:underline";
  return (
    <footer className="mt-20 border-t-2 border-encre bg-papier">
      <div className="mx-auto grid max-w-[1200px] gap-8 px-4 py-10 text-[14px] text-encre-douce sm:grid-cols-2 sm:px-6 lg:grid-cols-4">
        <div>
          <img src="/brand/logo.svg" alt="MangaStudio" className="h-8 w-auto" />
          <p className="mt-3 max-w-[260px]">{t("Votre idée, vos personnages, votre manga.", "Your idea, your characters, your manga.")}</p>
        </div>
        <nav aria-label={t("Plateforme", "Platform")}>
          <p className="label-caps mb-2 text-encre">{t("Plateforme", "Platform")}</p>
          <ul>
            <li><Link to="/" hash="tarifs" className={lien}>{t("Tarifs", "Pricing")}</Link></li>
            <li><Link to="/styles" className={lien}>{t("Les styles", "Styles")}</Link></li>
            <li><Link to="/galerie" className={lien}>{t("À lire", "Read")}</Link></li>
            <li><Link to="/concours" className={lien}>{t("Concours", "Contests")}</Link></li>
            <li><Link to="/abonnements" className={lien}>{t("Abonnements", "Plans")}</Link></li>
            <li><Link to="/inscription" className={lien}>{t("Créer un compte", "Sign up")}</Link></li>
          </ul>
        </nav>
        <nav aria-label={t("Aide", "Help")}>
          <p className="label-caps mb-2 text-encre">{t("Aide", "Help")}</p>
          <ul>
            <li><Link to="/faq" className={lien}>{t("Questions fréquentes", "FAQ")}</Link></li>
            <li><Link to="/contact" className={lien}>{t("Nous contacter", "Contact us")}</Link></li>
            <li><Link to="/mon-avis" className={lien}>{t("Donner mon avis", "Leave a review")}</Link></li>
            <li><Link to="/regles-publication" className={lien}>{t("Règles de publication", "Publishing rules")}</Link></li>
            <li><Link to="/gagner" className={lien}>{t("Gagner des crédits", "Earn credits")}</Link></li>
            <li><Link to="/soutenir" className={`${lien} font-bold text-vermillon`}>{t("Nous soutenir", "Support us")}</Link></li>
          </ul>
        </nav>
        <div>
          <p className="label-caps mb-2 text-encre">Contact</p>
          <ul className="flex flex-col gap-1">
            {CONTACT.email && <li><a href={`mailto:${CONTACT.email}`} className={`${lien} gap-2 break-all`}><Mail size={16} strokeWidth={2} aria-hidden />{CONTACT.email}</a></li>}
            {CONTACT.orange && <li><a href={telHref(CONTACT.orange)} className={`${lien} gap-2`}><Phone size={16} strokeWidth={2} aria-hidden /><span><span className="tabular">{CONTACT.orange}</span> (Orange)</span></a></li>}
            {CONTACT.mtn && <li><a href={telHref(CONTACT.mtn)} className={`${lien} gap-2`}><Phone size={16} strokeWidth={2} aria-hidden /><span><span className="tabular">{CONTACT.mtn}</span> (MTN)</span></a></li>}
            {!CONTACT.email && !CONTACT.orange && !CONTACT.mtn && <li><Link to="/contact" className={lien}>{t("Nous écrire", "Write to us")}</Link></li>}
          </ul>
        </div>
      </div>
      <p className="border-t border-trait py-4 text-center text-[13px] text-encre-douce">© {new Date().getFullYear()} MangaStudio · {t("un projet PsikaLab", "a PsikaLab project")}</p>
    </footer>
  );
}

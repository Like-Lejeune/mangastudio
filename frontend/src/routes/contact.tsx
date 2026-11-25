import { createFileRoute, Link } from "@tanstack/react-router";
import { Clock, Mail, MessageCircle, Phone } from "lucide-react";
import type { ReactNode } from "react";
import { CONTACT } from "@/content/contact";
import { telHref, whatsappHref } from "@/lib/contact";
import { Card, Container, PageTitle } from "@/components/ink";
import { tr } from "@/lib/i18n";

export const Route = createFileRoute("/contact")({
  head: () => ({ meta: [{ title: tr("Nous contacter — MangaStudio", "Contact us — MangaStudio") }, { name: "description", content: tr("Écrire ou appeler l'équipe MangaStudio.", "Write to or call the MangaStudio team.") }] }),
  component: ContactPage,
});

function Ligne({ icone, titre, children }: { icone: ReactNode; titre: string; children: ReactNode }) {
  return (
    <Card className="flex items-start gap-4">
      <span className="flex size-12 shrink-0 items-center justify-center rounded-full border-2 border-encre bg-soleil" aria-hidden>{icone}</span>
      <div className="min-w-0">
        <p className="label-caps">{titre}</p>
        <div className="mt-1 text-[18px] font-bold">{children}</div>
      </div>
    </Card>
  );
}

function Numero({ n, operateur }: { n: string; operateur: string }) {
  return (
    <Ligne icone={<Phone size={22} strokeWidth={2} />} titre={tr(`Téléphone ${operateur}`, `${operateur} phone`)}>
      <a href={telHref(n)} className="tabular underline">{n}</a>
      {CONTACT.whatsapp && (
        <a href={whatsappHref(n)} target="_blank" rel="noreferrer" className="mt-2 flex items-center gap-2 text-[15px] font-medium text-succes underline">
          <MessageCircle size={18} strokeWidth={2} aria-hidden />{tr("Écrire sur WhatsApp", "Message on WhatsApp")}
        </a>
      )}
    </Ligne>
  );
}

function ContactPage() {
  const rien = !CONTACT.email && !CONTACT.orange && !CONTACT.mtn;
  return (
    <Container className="max-w-[860px]">
      <PageTitle sub={<>{tr("Une question sur un épisode, un paiement ou votre compte ? Consultez d'abord les ", "A question about an episode, a payment or your account? First check the ")}<Link to="/faq" className="font-bold text-indigo underline">{tr("questions fréquentes", "FAQ")}</Link>{tr(", sinon contactez-nous.", ", otherwise contact us.")}</>}>
        {tr("Nous contacter", "Contact us")}
      </PageTitle>
      {rien ? (
        <p className="text-encre-douce">{tr("Nos coordonnées seront bientôt disponibles ici.", "Our contact details will be available here soon.")}</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {CONTACT.email && (
            <Ligne icone={<Mail size={22} strokeWidth={2} />} titre={tr("E-mail", "Email")}>
              <a href={`mailto:${CONTACT.email}`} className="break-all underline">{CONTACT.email}</a>
            </Ligne>
          )}
          {CONTACT.orange && <Numero n={CONTACT.orange} operateur="Orange" />}
          {CONTACT.mtn && <Numero n={CONTACT.mtn} operateur="MTN" />}
          {CONTACT.horaires && <Ligne icone={<Clock size={22} strokeWidth={2} />} titre={tr("Horaires", "Opening hours")}><span className="text-[16px] font-medium">{tr(CONTACT.horaires, CONTACT.horairesEn || CONTACT.horaires)}</span></Ligne>}
        </div>
      )}
      <p className="mt-8 text-[14px] leading-5 text-encre-douce">
        {tr("Pour un paiement, indiquez la date, le montant et le numéro utilisé : nous le retrouverons plus vite.", "For a payment, give the date, the amount and the number used: we'll find it faster.")}
      </p>
    </Container>
  );
}

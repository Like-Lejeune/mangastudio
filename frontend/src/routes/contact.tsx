import { createFileRoute, Link } from "@tanstack/react-router";
import { Clock, Mail, MessageCircle, Phone } from "lucide-react";
import type { ReactNode } from "react";
import { CONTACT } from "@/content/contact";
import { telHref, whatsappHref } from "@/lib/contact";
import { Card, Container, PageTitle } from "@/components/ink";

export const Route = createFileRoute("/contact")({
  head: () => ({ meta: [{ title: "Nous contacter — MangaStudio" }, { name: "description", content: "Écrire ou appeler l'équipe MangaStudio." }] }),
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
    <Ligne icone={<Phone size={22} strokeWidth={2} />} titre={`Téléphone ${operateur}`}>
      <a href={telHref(n)} className="tabular underline">{n}</a>
      {CONTACT.whatsapp && (
        <a href={whatsappHref(n)} target="_blank" rel="noreferrer" className="mt-2 flex items-center gap-2 text-[15px] font-medium text-succes underline">
          <MessageCircle size={18} strokeWidth={2} aria-hidden />Écrire sur WhatsApp
        </a>
      )}
    </Ligne>
  );
}

function ContactPage() {
  const rien = !CONTACT.email && !CONTACT.orange && !CONTACT.mtn;
  return (
    <Container className="max-w-[860px]">
      <PageTitle sub={<>Une question sur un épisode, un paiement ou votre compte ? Consultez d'abord les <Link to="/faq" className="font-bold text-indigo underline">questions fréquentes</Link>, sinon contactez-nous.</>}>
        Nous contacter
      </PageTitle>
      {rien ? (
        <p className="text-encre-douce">Nos coordonnées seront bientôt disponibles ici.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {CONTACT.email && (
            <Ligne icone={<Mail size={22} strokeWidth={2} />} titre="E-mail">
              <a href={`mailto:${CONTACT.email}`} className="break-all underline">{CONTACT.email}</a>
            </Ligne>
          )}
          {CONTACT.orange && <Numero n={CONTACT.orange} operateur="Orange" />}
          {CONTACT.mtn && <Numero n={CONTACT.mtn} operateur="MTN" />}
          {CONTACT.horaires && <Ligne icone={<Clock size={22} strokeWidth={2} />} titre="Horaires"><span className="text-[16px] font-medium">{CONTACT.horaires}</span></Ligne>}
        </div>
      )}
      <p className="mt-8 text-[14px] leading-5 text-encre-douce">
        Pour un paiement, indiquez la date, le montant et le numéro utilisé : nous le retrouverons plus vite.
      </p>
    </Container>
  );
}

/** Liens d'appel et WhatsApp à partir d'un numéro écrit librement (« +237 6 99 00 00 00 »). */
export const chiffres = (n: string) => n.replace(/[^\d+]/g, "");
export const telHref = (n: string) => `tel:${chiffres(n)}`;
export const whatsappHref = (n: string) => `https://wa.me/${chiffres(n).replace(/^\+/, "")}`;

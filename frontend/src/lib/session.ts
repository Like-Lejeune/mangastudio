import { useQuery } from "@tanstack/react-query";
import { useSyncExternalStore } from "react";
import { api, tokenStore, type Me } from "@/lib/api";

/** Le jeton de connexion : `null` si déconnecté, `undefined` tant qu'on ne sait pas (rendu côté serveur). */
export function useToken(): string | null | undefined {
  return useSyncExternalStore(tokenStore.subscribe, tokenStore.get, () => undefined);
}

/** Le compte connecté : plan, limites et solde de crédits. */
export function useMe() {
  const token = useToken();
  return useQuery({ queryKey: ["me"], queryFn: () => api<Me>("/me"), enabled: !!token });
}

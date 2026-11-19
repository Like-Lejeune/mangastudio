# Construit le front puis le sert avec Caddy, qui fait aussi le HTTPS et le relais vers l'API.
# Contexte de construction : la racine du projet (voir docker-compose.yml).
FROM node:20-alpine AS build
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ .
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM caddy:2-alpine
COPY Caddyfile Caddyfile.proxy /etc/caddy/
COPY --from=build /src/dist /srv/app
# CADDY_CONFIG choisit la variante : Caddyfile (Caddy fait le HTTPS) ou Caddyfile.proxy (derrière nginx).
CMD ["sh", "-c", "exec caddy run --config \"${CADDY_CONFIG:-/etc/caddy/Caddyfile}\" --adapter caddyfile"]

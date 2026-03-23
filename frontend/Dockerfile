# Etapa 1: build
FROM node:20-alpine AS builder

WORKDIR /app

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# Etapa 2: servir solo los estáticos (imagen mucho más pequeña)
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

ENV PORT=80

# Config de nginx para SPA + puerto dinámico (Render/Railway/Fly)
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80
# Etapa 1: build
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# Etapa 2: servir solo los estáticos (imagen mucho más pequeña)
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# Config de nginx para que React Router funcione
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
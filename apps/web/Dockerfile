FROM node:22-alpine AS builder
WORKDIR /app
COPY apps/web/package.json ./package.json
RUN npm install --no-audit --no-fund
COPY apps/web ./
RUN npm run build
FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -S web && adduser -S web -G web
COPY --from=builder --chown=web:web /app/.next/standalone ./
COPY --from=builder --chown=web:web /app/.next/static ./.next/static
USER web
EXPOSE 3000
CMD ["node","server.js"]

# Deploy to Google Cloud Run
# see: https://github.com/nextjs/deploy-google-cloud-run/blob/main/Dockerfile

FROM node:lts-alpine AS base

# Stage 1: Install dependencies
FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && \
    corepack prepare pnpm@9.15.5 --activate && \
    pnpm install --frozen-lockfile

# Stage 2: Build the application
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN corepack enable && \
    corepack prepare pnpm@9.15.5 --activate && \
    pnpm run build

# Stage 3: Production server
FROM base AS runner

WORKDIR /app

# Install dotenvx
RUN apk add --no-cache curl
RUN curl -sfS https://dotenvx.sh > install.sh \
    && chmod +x install.sh \
    && ./install.sh --directory=. \
    && rm install.sh

ENV NODE_ENV=production
COPY --from=builder /app/.env ./

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

# see: https://dotenvx.com/docs/platforms/docker
CMD ["./dotenvx", "run", "--env-file=.env", "--", "node", "server.js"]
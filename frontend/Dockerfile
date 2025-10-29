# Frontend Dockerfile for Cloud Run
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set build-time environment variable
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Echo the API URL to bust Docker cache when it changes
RUN echo "Building with API URL: $NEXT_PUBLIC_API_URL"

# Debug: Print env.ts validation section to verify correct source
RUN echo "=== Checking env.ts validation code ===" && \
    grep -A 5 "if (errors.length > 0)" src/config/env.ts || echo "Pattern not found"

# Clean any previous build artifacts and caches
RUN rm -rf .next .next/cache node_modules/.cache

# Clear npm cache to ensure fresh module resolution
RUN npm cache clean --force

# Build Next.js application with fresh cache
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set permissions for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

# Cloud Run expects the app to listen on $PORT
ENV PORT=8080
EXPOSE 8080

CMD ["node", "server.js"]

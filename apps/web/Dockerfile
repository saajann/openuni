# apps/web/Dockerfile
# ─────────────────────────────────────────────────────────────────────────────
# Local development Dockerfile for Next.js
# ─────────────────────────────────────────────────────────────────────────────

FROM node:20-alpine

WORKDIR /app

# Install dependencies first for caching
COPY package.json package-lock.json* ./
RUN npm install

# Copy application source
COPY . .

# Expose Next.js default port
EXPOSE 3000

# Run in development mode to support hot-reloading and dynamic env vars
CMD ["npm", "run", "dev"]

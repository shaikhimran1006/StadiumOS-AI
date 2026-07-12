# ============================================================================
# StadiumOS AI Frontend - Multi-stage Docker Build
# ============================================================================

# ----------------------------------------------------------------------------
# Stage 1: Build the React application
# ----------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests first for better layer caching
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies (clean install for reproducibility)
RUN npm ci --no-audit --no-fund

# Copy source code
COPY frontend/ .

# Build the production bundle
ARG VITE_API_URL=/api
ARG VITE_WS_URL=/api/ws
ARG VITE_APP_VERSION=1.0.0
ARG NODE_ENV=production

ENV VITE_API_URL=$VITE_API_URL \
    VITE_WS_URL=$VITE_WS_URL \
    VITE_APP_VERSION=$VITE_APP_VERSION \
    NODE_ENV=$NODE_ENV

RUN npm run build

# Verify build output exists
RUN test -d /app/dist && echo "Build output verified"

# ----------------------------------------------------------------------------
# Stage 2: Serve with Nginx
# ----------------------------------------------------------------------------
FROM nginx:1.27-alpine AS runtime

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Install curl for health checks
RUN apk add --no-cache curl

# Copy custom nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Create nginx cache directories
RUN mkdir -p /var/cache/nginx/client_temp \
             /var/cache/nginx/proxy_temp \
             /var/cache/nginx/fastcgi_temp && \
    chown -R nginx:nginx /var/cache/nginx

# Non-root is not possible with stock nginx image since nginx
# binds to port 80 and needs root for that. The Cloud Run proxy handles TLS.

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Run nginx in foreground
CMD ["nginx", "-g", "daemon off;"]

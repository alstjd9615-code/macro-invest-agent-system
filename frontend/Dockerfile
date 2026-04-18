# =============================================================================
# macro-invest-agent-platform — frontend image (static files via nginx)
# Build context: project root
# =============================================================================

FROM nginx:1.27-alpine

# Install curl for healthcheck
RUN apk add --no-cache curl

# Remove default nginx content
RUN rm -rf /usr/share/nginx/html/*

# Copy static frontend assets
COPY frontend/ /usr/share/nginx/html/

# Lightweight healthcheck
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

EXPOSE 80

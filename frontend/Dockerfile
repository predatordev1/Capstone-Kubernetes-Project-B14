# ─── Stage 1: Build React application ───────────────────────────────────────
# We use node:18-alpine because:
# - alpine = minimal Linux (~5MB base vs ~200MB full Ubuntu)
# - node:18 = LTS version, stable and well-supported
# - "build" label allows Stage 2 to reference Stage 1 output
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files FIRST, then install, then copy source
# This is the critical layer caching pattern:
# - package.json changes rarely (only when adding packages)
# - Source code changes on every commit
# - Docker caches the npm install layer until package.json changes
# - Result: npm install only runs when you add/remove packages
#           not on every single code change
COPY package*.json ./
RUN npm install

# Build arguments — these come from Jenkins pipeline --build-arg flags
# They MUST be declared as ARG before they can be used as ENV
# ARG = available only during docker build
# ENV = baked into the image and available at runtime
ARG REACT_APP_AUTH_API_URL
ARG REACT_APP_STREAMING_API_URL
ARG REACT_APP_STREAMING_PUBLIC_URL
ARG REACT_APP_ADMIN_API_URL
ARG REACT_APP_CHAT_API_URL
ARG REACT_APP_CHAT_SOCKET_URL

# Convert build args to environment variables
# React's build tool (react-scripts) reads REACT_APP_* env vars
# and replaces them inline in the JavaScript bundle at build time
# This is why the ALB URL must be known BEFORE building the image
ENV REACT_APP_AUTH_API_URL=${REACT_APP_AUTH_API_URL}
ENV REACT_APP_STREAMING_API_URL=${REACT_APP_STREAMING_API_URL}
ENV REACT_APP_STREAMING_PUBLIC_URL=${REACT_APP_STREAMING_PUBLIC_URL}
ENV REACT_APP_ADMIN_API_URL=${REACT_APP_ADMIN_API_URL}
ENV REACT_APP_CHAT_API_URL=${REACT_APP_CHAT_API_URL}
ENV REACT_APP_CHAT_SOCKET_URL=${REACT_APP_CHAT_SOCKET_URL}

# Copy source and build
COPY . .
RUN npm run build
# Output: /app/build/ contains compiled HTML, CSS, JS bundle

# ─── Stage 2: Serve with Nginx ───────────────────────────────────────────────
# We throw away the entire node:18-alpine stage here
# The final image contains ONLY nginx + the compiled static files
# Result: ~23MB image instead of ~400MB if we used node to serve
FROM nginx:1.27-alpine AS production

# Copy only the compiled output from Stage 1 — not node_modules, not source
COPY --from=build /app/build /usr/share/nginx/html

# Copy our custom nginx config which adds:
# - React Router support (try_files)
# - Gzip compression
# - Security headers
# - Health check endpoint for Kubernetes probes
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

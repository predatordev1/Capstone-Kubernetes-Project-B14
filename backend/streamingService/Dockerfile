# Single-stage build for Node.js backend service
# alpine = minimal image (~5MB base vs ~200MB full)
# node:18 = LTS, stable, matches development environment
FROM node:18-alpine AS production

WORKDIR /app

# Layer caching pattern: install deps before copying source
# npm install is cached until package.json changes
COPY package*.json ./
RUN npm install --production

# Copy application source code
# Changes here do NOT invalidate the npm install cache above
COPY . .

# NODE_ENV=production affects:
# - Some packages enable optimizations
# - Express.js caches views and disables detailed errors
# - Reduces memory usage in several npm packages
ENV NODE_ENV=production

EXPOSE 3002

# Use exec form (JSON array) not shell form (string)
# Exec form: signals (SIGTERM from kubectl stop) go directly to node
# Shell form: signals go to /bin/sh which may not forward them
# Result: graceful shutdown works correctly with exec form
CMD ["npm", "run", "start"]

# Base image légère
FROM python:3.11-slim

# Working directory
WORKDIR /app

# Copy requirements Python
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir semgrep

# Install Node.js 22.x — requis par Prisma 7 (@prisma/streams-local nécessite Node >= 22)
RUN apt-get update && \
    apt-get install -y ca-certificates curl gnupg && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs

# Install JS AST tooling for P3 guards (dev.py AST engine path)
RUN npm install -g ts-morph @typescript-eslint/parser @typescript-eslint/typescript-estree

# Install Prisma CLI globally (Phase 0 X1)
# Keep major aligned with project templates using Prisma 7.
RUN npm install -g prisma@7

# Install Docker CLI client
RUN apt-get update && \
    apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli



# Copy le code usine
RUN find . -name "*.pyc" -delete
COPY . .

# Install ts-morph locally for tsc_check.mjs (R1 — structured TS diagnostics)
RUN cd /app/tools/ts && npm install --production

# T4 — Pre-install Next.js/Clerk/Prisma stack deps so each project run uses cp (~3s) instead of npm install (~40s)
# The template package.json is stack-specific but dependency-pinned — all generated projects share the same deps.
COPY config/stacks/nextjs-clerk-prisma/templates/package.json /app/npm_cache/package.json
RUN cd /app/npm_cache && npm install

# Commande de démarrage
CMD ["python", "run/worker.py"]

# Base image légère
FROM python:3.11-slim

# Working directory
WORKDIR /app

# Copy requirements Python
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js 20.x
RUN apt-get update && \
    apt-get install -y ca-certificates curl gnupg && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs

# === Dépendances système pour Puppeteer / mermaid-cli ===
RUN apt-get update && \
    apt-get install -y \
        ca-certificates \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libc6 \
        libcairo2 \
        libcups2 \
        libdbus-1-3 \
        libexpat1 \
        libfontconfig1 \
        libgbm1 \
        libgcc1 \
        libglib2.0-0 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libstdc++6 \
        libx11-6 \
        libxcomposite1 \
        libxcursor1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxi6 \
        libxrandr2 \
        libxrender1 \
        libxtst6 \
        lsb-release \
        wget \
        xdg-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Jest + testing libs + mermaid-cli globalement
RUN npm install -g jest @testing-library/react @testing-library/jest-dom \
    babel-jest @babel/preset-env @babel/preset-react ts-jest typescript \
    @mermaid-js/mermaid-cli

# Copy le code usine
RUN find . -name "*.pyc" -delete
COPY . .

# Commande de démarrage
CMD ["python", "run/worker.py"]
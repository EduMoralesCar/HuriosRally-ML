FROM python:3.11-slim

WORKDIR /app

# Instalar Node.js 20 y git para el conector de WhatsApp Real (Baileys)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY whatsapp_bridge/package.json whatsapp_bridge/package.json
RUN npm --prefix whatsapp_bridge install --omit=dev

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]

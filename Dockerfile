FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV WORKSPACE_PATH=/data/workspaces
ENV LOG_LEVEL=INFO

RUN apt-get update && apt-get install -y --no-install-recommends \
    tmux \
    curl \
    ca-certificates \
    supervisor \
    unzip \
    git \
    nodejs \
    npm \
 && npm install -g opencode-ai \
 && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash appuser \
 && mkdir -p /data/workspaces /data/bin /data/logs \
 && chown -R appuser:appuser /data

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN chmod +x /app/scripts/*.sh || true

EXPOSE 7860

ENTRYPOINT ["/app/scripts/entrypoint.sh"]


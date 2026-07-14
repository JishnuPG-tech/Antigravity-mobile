FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV WORKSPACE_PATH=/data/workspaces

RUN apt-get update && apt-get install -y --no-install-recommends \
    tmux \
    curl \
    ca-certificates \
    supervisor \
    unzip \
    gcc \
    make \
 && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash appuser || true

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN chmod +x /app/scripts/install_antigravity.sh || true
RUN mkdir -p /data && mkdir -p /data/workspaces && chown -R appuser:appuser /data

# Expose Hugging Face Spaces default port
EXPOSE 7860

COPY scripts/entrypoint.sh /app/scripts/entrypoint.sh
RUN chmod +x /app/scripts/entrypoint.sh

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl \
       ca-certificates \
       tmux \
       git \
       unzip \
       build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app

# Install Antigravity CLI in container (non-interactive)
RUN chmod +x /app/scripts/install_antigravity.sh && /app/scripts/install_antigravity.sh || true

ENV PATH="/root/.local/bin:${PATH}"

EXPOSE 8000

CMD ["/usr/bin/supervisord", "-c", "/app/config/supervisord.conf"]

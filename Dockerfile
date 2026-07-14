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
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN chmod +x /app/scripts/install_antigravity.sh /app/scripts/entrypoint.sh || true
RUN mkdir -p /data/workspaces /data/bin /data/logs

EXPOSE 7860

ENTRYPOINT ["/app/scripts/entrypoint.sh"]

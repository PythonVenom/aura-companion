# Aura Docker image (T075)
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        pipewire pipewire-pulse pulseaudio-utils \
        libsndfile1 ffmpeg portaudio19-dev build-essential \
        mpv socat curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY aura/ ./aura/
COPY aura_main.py run_aura.sh ./
COPY tools/ ./tools/
RUN pip install --no-cache-dir .

ENV AURA_CACHE_DIR=/data/cache \
    AURA_CONFIG_DIR=/data/config \
    PYTHONUNBUFFERED=1

VOLUME ["/data"]
EXPOSE 8765

# Ollama host (external container or host)
ENV OLLAMA_HOST=http://ollama:11434

CMD ["python3", "aura_main.py"]

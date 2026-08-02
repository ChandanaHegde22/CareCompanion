# ══════════════════════════════════════════════════════════════════════════════
#  CareCompanion – Dockerfile
#  Multi-stage build for a lean production image
# ══════════════════════════════════════════════════════════════════════════════

# ── Stage 1: base image ───────────────────────────────────────────────────────
FROM python:3.11-slim AS base

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libsqlite3-dev \
        libffi-dev \
        portaudio19-dev \
        ffmpeg \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-hin \
        tesseract-ocr-kan \
        libtesseract-dev \
        poppler-utils \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# ── Stage 2: Python deps ──────────────────────────────────────────────────────
FROM base AS deps

WORKDIR /install

# Copy and install requirements
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model so it's baked in
RUN python -c "from sentence_transformers import SentenceTransformer; \
               SentenceTransformer('all-MiniLM-L6-v2')" || true

# ── Stage 3: production ───────────────────────────────────────────────────────
FROM deps AS production

WORKDIR /app

# Copy application code
COPY . .

# Create runtime directories
RUN mkdir -p uploads vector_store logs database

# Non-root user for security
RUN useradd -m -u 1000 carecompanion && \
    chown -R carecompanion:carecompanion /app

USER carecompanion

# Expose Streamlit port
EXPOSE 8501

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Streamlit configuration via environment
ENV STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_THEME_BASE=light \
    STREAMLIT_THEME_PRIMARY_COLOR="#6C63FF" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Entry point
ENTRYPOINT ["streamlit", "run", "app.py", \
            "--server.port=8501", \
            "--server.address=0.0.0.0", \
            "--server.headless=true", \
            "--browser.gatherUsageStats=false"]

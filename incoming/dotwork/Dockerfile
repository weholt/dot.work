# Multi-stage build for optimized Docker image

# ===========================================
# BUILD STAGE
# Purpose: Install dependencies in isolated environment
# ===========================================
FROM python:3.13-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager for faster dependency resolution
RUN pip install uv

# Copy dependency manifests first (enables layer caching)
COPY pyproject.toml ./
COPY README.md ./

# Create virtual environment and install minimal dependencies
# This layer is cached until pyproject.toml changes
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python -e .

# ===========================================
# RUNTIME STAGE
# Purpose: Minimal production image with only runtime dependencies
# ===========================================
FROM python:3.13-slim AS runtime

# Set working directory
WORKDIR /app

# Install runtime system dependencies
# - curl: for healthcheck endpoint testing
# - git: required by GitPython for repository management
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create model cache directory with global read permissions
# This allows the non-root user to access models downloaded as root
RUN mkdir -p /root/.cache/huggingface && chmod -R 755 /root/.cache

# Download embedding model in separate cacheable layer
# This ensures model (~500MB) is cached and not re-downloaded on code changes
# Positioned BEFORE copying application code for optimal cache efficiency
RUN /opt/venv/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code (changes frequently, so positioned after model download)
COPY solace/ ./solace/

# Copy .env file if it exists (optional)
COPY .env* ./

# Create non-root user for security
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -s /bin/bash -m appuser

# Create directories with proper permissions
# /data - for document storage (mounted as volume)
# /data/.solace - for persistence data (ChromaDB, etc.)
# /app/data - fallback local directory
# /home/appuser/.cache - for user cache files
RUN mkdir -p /data /data/.solace /app/data /home/appuser/.cache && \
    chown -R appuser:appgroup /app /data /home/appuser/.cache

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 9765
EXPOSE 9766

# Set environment variables with secure defaults (can be overridden by .env)
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV DOCS_DIR=/data
ENV PERSIST_DIR=/data/.solace
ENV HOST=0.0.0.0
ENV PORT=9765
ENV WEB_PORT=9766
ENV MODEL_NAME=all-MiniLM-L6-v2
ENV TEMPLATE_THEME=default
ENV DOCKER_ENV=true
ENV PYTHONUNBUFFERED=1

# Health check with curl on web interface port
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${WEB_PORT:-9766}/view || exit 1

# Run the unified server (works for both local and Docker)
CMD ["python", "-m", "solace.server"]
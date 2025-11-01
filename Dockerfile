### Multi-stage Dockerfile optimized for faster rebuilds
### Stage 1: builder (build wheels for Python packages)
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies required to build wheels for many packages.
# Keep these only in the builder stage so the final image stays small.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       git \
       curl \
       wget \
       ca-certificates \
       libssl-dev \
       libffi-dev \
       python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /wheels_build

# Copy only requirements first to leverage Docker layer cache when requirements
# don't change.
COPY requirements.txt ./requirements.txt

# Build wheels into /wheels. This compiles heavy packages once during build.
RUN pip install --upgrade pip setuptools wheel && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


### Stage 2: final image (runtime)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Minimal runtime deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy pre-built wheels from builder stage and install from wheels to avoid
# rebuilding on each image create. --no-index + --find-links tells pip to
# prefer the provided wheels.
COPY --from=builder /wheels /wheels
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --prefer-binary --no-index --find-links /wheels -r requirements.txt

# Copy application code
COPY . /app

EXPOSE 8010 3000

# Default command (override in docker-compose if desired)
CMD ["python", "main.py"]   

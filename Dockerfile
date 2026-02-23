FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

WORKDIR /app

# Install Python runtime dependencies in the container image.
COPY pyproject.toml uv.lock README.md ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir 'playwright==1.58.0'

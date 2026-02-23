FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

WORKDIR /app

# Install uv from the official distroless image.
COPY --from=ghcr.io/astral-sh/uv:0.8.13 /uv /uvx /usr/local/bin/

# Keep the synced virtualenv outside the bind-mounted /app workspace.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

# Resolve and install locked runtime dependencies for container execution.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-install-project

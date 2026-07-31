FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PUID=1000 \
    PGID=1000

# OCI labels (filled further by CI via --label / metadata-action)
LABEL org.opencontainers.image.title="random-recipe" \
      org.opencontainers.image.description="Random recipe picker for homelab Docker" \
      org.opencontainers.image.source="https://github.com/patrickthescriptwhisperer/random-recipe" \
      org.opencontainers.image.licenses="MIT"

COPY requirements.txt .
RUN apt-get update \
    && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 1000 --shell /usr/sbin/nologin appuser

COPY app.py recipes.py ./
COPY docker-entrypoint.sh /docker-entrypoint.sh
COPY data ./data
COPY templates ./templates
COPY static ./static

# Image ships an empty recipe list; mount ./data at runtime for real content.
# Entrypoint remaps appuser to PUID/PGID and fixes /app/data ownership.
RUN printf '[]\n' > /app/data/recipes.json \
    && chmod +x /docker-entrypoint.sh \
    && chown -R appuser:appuser /app

# Start as root so the entrypoint can honor PUID/PGID, then drop privileges.
# Override with compose `user:` if you prefer to skip remapping.
ENTRYPOINT ["/docker-entrypoint.sh"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "app:app"]

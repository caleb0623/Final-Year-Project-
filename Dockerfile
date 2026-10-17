# Attire Checker: one container serves the website pages, the browser/Android API and the AI models.
# Works on Hugging Face Spaces (Docker) and Render. Secrets come from the host's environment settings.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860

RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Run as a non-root user (required by Hugging Face Spaces, good practice elsewhere).
RUN useradd --create-home --uid 1000 app
WORKDIR /home/app/web

# CPU-only PyTorch (much smaller than the default CUDA build), then the rest.
COPY requirements.txt .
RUN pip install "torch>=1.12.0,<2.6" "torchvision>=0.13.0,<0.21" --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt gunicorn

COPY --chown=app:app . .
USER app

# Model files are not in git: they are downloaded from the private Supabase bucket (models/) on start.
ENV ATTIRE_BEHIND_PROXY=1 \
    ATTIRE_WEB_HTTPS=1 \
    ATTIRE_WARM_UP=1

EXPOSE 7860
# One worker keeps a single copy of the models in memory; threads serve concurrent requests.
CMD gunicorn web_app:app --bind 0.0.0.0:${PORT} --workers 1 --threads 8 --timeout 300

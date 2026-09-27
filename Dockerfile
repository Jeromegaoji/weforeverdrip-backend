# ── WEFOREVERDRIP Backend ─────────────────────────────────────────────────────
#
# python:3.13-slim: minimal Debian-based image with Python 3.13 pre-installed.
# "slim" strips docs, tests, and dev tools — keeps image ~130 MB vs ~900 MB full.
#
FROM python:3.13-slim

# PYTHONDONTWRITEBYTECODE=1  → skip generating .pyc files (useless in containers)
# PYTHONUNBUFFERED=1         → flush stdout/stderr immediately (logs appear instantly)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Tell Django which settings module to use at runtime.
# settings_production.py inherits base settings and adds:
#   - SSL/HSTS security headers
#   - DATABASE_URL-based config (reads one Neon connection string)
#   - DEBUG=False
ENV DJANGO_SETTINGS_MODULE=weforeverdrip_backend.settings_production

WORKDIR /app

# ── Install Python dependencies ───────────────────────────────────────────────
#
# Copy requirements.txt BEFORE the source code.
# Docker builds in layers and caches each one. If requirements.txt hasn't
# changed between deploys, Docker skips pip install entirely — saving minutes.
# Changing a .py file won't invalidate the pip cache layer.
#
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy source code ───────────────────────────────────────────────────────────
COPY . .

# ── Collect static files ──────────────────────────────────────────────────────
#
# Run collectstatic at BUILD time, not container startup time.
# Result: every container starts instantly. WhiteNoise serves these
# files directly from the container — no separate Nginx needed.
#
# Why the dummy env vars?
# python-decouple raises UndefinedValueError if SECRET_KEY is missing on
# import. dj-database-url needs DATABASE_URL to be a parseable connection
# string. These dummy values satisfy Django's import checks.
# collectstatic itself never reads either value — it only needs STATIC_ROOT.
# The REAL secrets are injected by Fly.io at container startup, not here.
#
RUN SECRET_KEY=build-time-placeholder \
    DATABASE_URL=postgres://placeholder:placeholder@localhost/placeholder \
    python manage.py collectstatic --noinput

EXPOSE 8000

# ── Start Gunicorn ─────────────────────────────────────────────────────────────
#
# Gunicorn is the production WSGI server. Never use `runserver` in production.
#
# --workers 2   two worker processes
# --threads 2   two threads per worker → up to 4 concurrent requests
# --timeout 120 kill workers that take more than 2 min (prevents memory hangs)
#
# This config suits Fly.io's free tier (1 shared CPU, 256 MB RAM).
#
CMD ["gunicorn", "weforeverdrip_backend.wsgi", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--threads", "2", \
     "--timeout", "120"]

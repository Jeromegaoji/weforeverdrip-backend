"""
Production settings for WEFOREVERDRIP backend.
Inherits from base settings.py and overrides for production.
"""

from .settings import *  # noqa: F401, F403
import dj_database_url
from decouple import config, Csv

# ── Core ────────────────────────────────────────────────────
DEBUG = False
SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=Csv())

# ── Database ─────────────────────────────────────────────────
DATABASES = {
    'default': dj_database_url.config(
        env='DATABASE_URL',
        conn_max_age=600,
        ssl_require=True
    )
}

# ── Static files ──────────────────────────────────────────────
# WhiteNoise is already present in MIDDLEWARE from base settings.py.
# Do NOT prepend it again here — that made it run twice on every request.
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ── Security ──────────────────────────────────────────────────
# SECURE_SSL_REDIRECT must be False when behind Railway / Render / Fly.io.
# Those platforms terminate SSL at their load balancer and forward requests
# to Django as plain HTTP internally.  Setting this True causes an infinite
# redirect loop.  Instead we trust the X-Forwarded-Proto header the proxy sets.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ── CORS & CSRF ───────────────────────────────────────────────
# Set both in your production .env — no hardcoded URLs.
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000',
    cast=Csv()
)

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:3000',
    cast=Csv()
)

# ── Logging ───────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

"""
Production settings for WEFOREVERDRIP backend.
Inherits from base settings and overrides for production environment.
"""

from .settings import *  # noqa: F401, F403
import dj_database_url
from decouple import config

# ============================================================================
# PRODUCTION DEBUG MODE
# ============================================================================
DEBUG = False

# ============================================================================
# SECRET KEY - MUST be set via environment variable
# ============================================================================
SECRET_KEY = config('SECRET_KEY')

# ============================================================================
# ALLOWED HOSTS - read from environment, comma-separated
# ============================================================================
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

# ============================================================================
# DATABASE - Parse DATABASE_URL provided by Railway PostgreSQL
# ============================================================================
DATABASES = {
    'default': dj_database_url.config(
        env='DATABASE_URL',
        conn_max_age=600,
        ssl_require=True
    )
}

# ============================================================================
# STATIC FILES - WhiteNoise middleware for efficient static file serving
# ============================================================================
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
] + MIDDLEWARE

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ============================================================================
# SECURITY HEADERS - HTTPS and Security
# ============================================================================
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ============================================================================
# CORS - Accept production domain (from environment)
# ============================================================================
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000'
).split(',')

# ============================================================================
# LOGGING - Basic console logging for production
# ============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

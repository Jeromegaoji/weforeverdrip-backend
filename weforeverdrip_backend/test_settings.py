"""
Test settings - use SQLite for testing to avoid PostgreSQL permission issues.
This file is only used when running tests.
"""
from weforeverdrip_backend.settings import *

# Use SQLite for tests instead of PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable some logging for cleaner test output
if 'LOGGING' in dir():
    LOGGING['loggers']['django']['level'] = 'WARNING'

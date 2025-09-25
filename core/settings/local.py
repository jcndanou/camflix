"""
Local development settings for CamFlix project.
"""

from .base import *

# Debug
DEBUG = True

# Database - Using SQLite for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'ATOMIC_REQUESTS': True,
    }
}

# Django Debug Toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Debug Toolbar Config
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
    'SHOW_TEMPLATE_CONTEXT': True,
    'ENABLE_STACKTRACES': True,
}

# Email Backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Django Extensions
SHELL_PLUS_IMPORTS = [
    'from apps.accounts.models import *',
    'from apps.movies.models import *',
    'from apps.ratings.models import *',
    'from apps.recommendations.models import *',
]

# Celery Configuration for Windows development
# Use threading instead of multiprocessing on Windows
CELERY_TASK_ALWAYS_EAGER = True  # Execute tasks synchronously in development
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'redis://localhost:6380/2'
CELERY_RESULT_BACKEND = 'redis://localhost:6380/3'

# For Windows, use solo pool or eventlet
import platform
if platform.system() == 'Windows':
    CELERY_TASK_ALWAYS_EAGER = True  # Run tasks synchronously on Windows
    CELERY_TASK_EAGER_PROPAGATES = True

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Static files
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Disable SSL redirect
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# SQL Query Logging
LOGGING['loggers']['django.db.backends'] = {
    'level': 'DEBUG',
    'handlers': ['console'],
    'propagate': False,
}
# -*- coding: utf-8 -*-
'''
Local settings

- Run in Debug mode
- Use console backend for emails
- Add Django Debug Toolbar
- Add django-extensions as app
'''

import sys
from .common import *  # noqa

# DEBUG
# ------------------------------------------------------------------------------
DEBUG = env.bool('DJANGO_DEBUG', default=True)
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Note: This key only used for development and testing.
SECRET_KEY = env("DJANGO_SECRET_KEY", default='app+3@gy#4^%e+z4-rsyflm&%27u*u**)q+jj+*2fer3d7_6^&')

# Mail settings
# ------------------------------------------------------------------------------
EMAIL_HOST = env("EMAIL_HOST", default='mailhog')
EMAIL_PORT = 1025


# CACHING
# ------------------------------------------------------------------------------
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': ''
    }
}

# LOGGING
# ------------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'root': {
        'level': 'DEBUG',
        'handlers': ['console'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)-8s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
        'simple': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(bold_white)s[%(asctime)s]%(log_color)s %(levelname)-8s%(reset)s %(message)s',
            'log_colors': {
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            'datefmt': '%H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'st_logfile': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': LOGS_DIR("spistresci.log"),
            'when': 'd',
            'formatter': 'verbose',
            'interval': 1,
            'backupCount': 7,
        }
    },
    'loggers': {
        'spistresci': {
            'level': 'DEBUG',
            'handlers': ['console', 'st_logfile'],
            'propagate': False,
        }
    },
}

if len(sys.argv) > 1 and sys.argv[1] == 'test':
    # during tests don't log on console or to file
    del LOGGING['loggers']['spistresci']

    LOGGING['formatters']['info_about_assert_logs'] = {
        '()': 'colorlog.ColoredFormatter',
        'format': '\n%(red)sEvery log on WARNING level or above should be catched with assertLogs in tests!%(reset)s'
                  '\n\n%(bold_white)s[%(asctime)s]%(log_color)s %(levelname)-8s%(reset)s %(message)s',
        'log_colors': {
          'DEBUG': 'cyan',
          'INFO': 'green',
          'WARNING': 'yellow',
          'ERROR': 'red',
          'CRITICAL': 'red,bg_white',
        },
        'datefmt': '%H:%M:%S'
    }

    LOGGING['handlers']['test_console'] = {
        'level': 'WARNING',
        'class': 'logging.StreamHandler',
        'formatter': 'info_about_assert_logs'
    }

    LOGGING['root'] = {
        'level': 'DEBUG',
        'handlers': ['test_console'],
    }


# django-debug-toolbar
# ------------------------------------------------------------------------------
MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
INSTALLED_APPS += ('debug_toolbar', )

INTERNAL_IPS = ('127.0.0.1', '10.0.2.2',)

DEBUG_TOOLBAR_CONFIG = {
    'DISABLE_PANELS': [
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ],
    'SHOW_TEMPLATE_CONTEXT': True,
}

# django-extensions
# ------------------------------------------------------------------------------
INSTALLED_APPS += ('django_extensions', )

########## CELERY
# In development, all tasks will be executed locally by blocking until the task returns
CELERY_ALWAYS_EAGER = True
########## END CELERY

# Your local stuff: Below this line define 3rd party library settings

# Django-chroniker
BASE_URL='http://localhost:8000'
CHRONIKER_EMAIL_SENDER = 'Chroniker'
CHRONIKER_EMAIL_HOST_USER = 'chroniker@localhost'

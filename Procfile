web: gunicorn config.wsgi:application
worker: celery worker --app=spistresci.taskapp --loglevel=info

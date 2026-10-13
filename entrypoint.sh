#!/bin/sh
set -e
case "$1" in
  web)
    python manage.py migrate --noinput
    if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
      python manage.py createsuperuser --noinput --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" 2>/dev/null || true
    fi
    exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60 --access-logfile -
    ;;
  worker)
    # espera a que el pod web haya creado las tablas
    until python manage.py migrate --check >/dev/null 2>&1; do echo "esperando migraciones..."; sleep 3; done
    exec python manage.py run_worker
    ;;
  *) exec "$@" ;;
esac

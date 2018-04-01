#!/usr/bin/env bash

# environment variables that can be set to control this entrypoint:
#   DJANGO_COLLECTSTATIC
#   DJANGO_MIGRATE
#   DJANGO_COLLECTSTATIC_LEADERONLY
#   DJANGO_MIGRATE_LEADERONLY

# Detect whether the container is denoted as a "leader"
# For multi-instance deployments, create /tmp/leader/is_leader (volume mount
# can be used) to denote the single container that should run admin commands

if [ -f /tmp/leader/is_leader ]; then
    IS_LEADER=1
    echo "Leader marker detected"
fi

# Run collectstatic command if either:
# - DJANGO_COLLECTSTATIC is present
# - Leader marker detected and DJANGO_COLLECTSTATIC_LEADERONLY is present

if [[ $DJANGO_COLLECTSTATIC || ( $IS_LEADER && $DJANGO_COLLECTSTATIC_LEADERONLY) ]]; then
    echo "Running Django collectstatic"
    python manage.py collectstatic -c --noinput
else
    echo "Skipping Django collectstatic"
fi

# Run migrate command if either:
# - DJANGO_MIGRATE is present
# - Leader marker detected and DJANGO_MIGRATE_LEADERONLY is present

if [[ $DJANGO_MIGRATE || ( $IS_LEADER && $DJANGO_MIGRATE_LEADERONLY) ]]; then
    echo "Running Django migrate"
    python manage.py migrate --noinput
else
    echo "Skipping Django migrate"
fi

# Run launch command based on first argument:
# "web" or no first argument: creates web container

if [ "$1" = "web" ] || [ -z "$1" ]; then
    echo "Starting web container ..."
    /usr/local/bin/gunicorn config.wsgi:application \
        -w 3 \
        -b :8000 \
        --error-logfile=- \
        --log-level=debug \
        --access-logfile=-
elif [ "$1" = "sslserver" ]; then
    echo "Starting sslserver for local development ..."
    python manage.py runsslserver 0.0.0.0:8000
elif [ "$1" = "runserver" ]; then
    echo "Running with manage.py runserver ..."
    python manage.py runserver 0.0.0.0:8000
else
    echo "Command type not recognized"
    exit 1
fi

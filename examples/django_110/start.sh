#!/usr/bin/env bash
(
    SCRIPT_DIR=$( cd $(dirname $0) ; pwd -P )
    cd "$SCRIPT_DIR"

    unset DJANGO_SETTINGS_MODULE
    source ./.virtualenv/bin/activate
    python manage.py runserver
)

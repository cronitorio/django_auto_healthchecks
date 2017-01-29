#!/usr/bin/env bash
SCRIPT_DIR=$( cd $(dirname $0) ; pwd -P )
cd "$SCRIPT_DIR/example"

unset DJANGO_SETTINGS_MODULE
source ./venv/bin/activate
python mysite/manage.py runserver

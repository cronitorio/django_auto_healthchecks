#!/usr/bin/env bash
(
    SCRIPT_DIR=$( cd $(dirname $0) ; pwd -P )
    cd "$SCRIPT_DIR"

    pip -V &> /dev/null || echo "ERROR: PIP is Required"
    virtualenv --version &> /dev/null || pip install virtualenv
    virtualenv .virtualenv
    source ./.virtualenv/bin/activate
    pip install -r requirements.txt

    ## Install the local version of the SDK..
    pip install --editable "file:///$SCRIPT_DIR/../../"
    unset DJANGO_SETTINGS_MODULE
    python manage.py migrate
)

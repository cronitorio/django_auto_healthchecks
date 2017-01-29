#!/usr/bin/env bash
(SCRIPT_DIR=$( cd $(dirname $0) ; pwd -P )
cd "$SCRIPT_DIR/example"

pip -V &> /dev/null || echo "ERROR: PIP is Required"
virtualenv --version &> /dev/null || pip install virtualenv
virtualenv --no-setuptools venv
source ./venv/bin/activate
pip install -r requirements.txt

## Install the local version of the SDK..
unlink ./venv/lib/python2.7/site-packages/django_auto_healthchecks
ln -s "$SCRIPT_DIR/src" ./venv/lib/python2.7/site-packages/django_auto_healthchecks
pip install -r ../requirements.txt
)

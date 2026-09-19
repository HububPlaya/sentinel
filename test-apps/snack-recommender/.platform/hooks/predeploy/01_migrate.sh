#!/bin/bash
set -e
source /var/app/venv/*/bin/activate
cd /var/app/staging
flask --app wsgi db upgrade

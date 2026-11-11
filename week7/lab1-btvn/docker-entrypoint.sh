#!/bin/sh
set -eu

flask --app wsgi:app db upgrade
exec "$@"

#!/bin/sh
set -e
gunicorn --bind "127.0.0.1:8080" main:application &
PID=$!
nginx -g "daemon off;"
kill $PID

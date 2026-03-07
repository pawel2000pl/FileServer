#!/bin/sh
set -e
touch /var/log/nginx/gunicorn_logs.txt /var/log/nginx/nginx_additional_logs.txt /var/log/nginx/access.log /var/log/nginx/error.log
USE_X_ACCEL_REDIRECT=TRUE gunicorn -b "unix:/run/gunicorn.sock" main:application >/var/log/nginx/gunicorn_logs.txt 2>&1 &
GUNICORN=$!
nginx -g "daemon off;" >/var/log/nginx/nginx_additional_logs.txt 2>&1 &
NGINX=$!
tail -f /var/log/nginx/gunicorn_logs.txt /var/log/nginx/nginx_additional_logs.txt /var/log/nginx/access.log /var/log/nginx/error.log
kill $NGINX
kill $GUNICORN

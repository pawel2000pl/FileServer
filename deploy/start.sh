#!/bin/sh
set -e
gunicorn --bind "127.0.0.1:8080" main:application > /var/log/nginx/gunicorn_logs.txt &
GUNICORN=$!
nginx -g "daemon off;" > /var/log/nginx/nginx_additional_logs.txt &
NGINX=$!
tail -f /var/log/nginx/gunicorn_logs.txt /var/log/nginx/nginx_additional_logs.txt /var/log/nginx/access.log /var/log/nginx/error.log
kill $NGINX
kill $GUNICORN

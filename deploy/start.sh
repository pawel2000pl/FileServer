#!/bin/sh
set -e
touch /var/log/nginx/gunicorn_logs.txt /var/log/nginx/nginx_additional_logs.txt /var/log/nginx/access.log /var/log/nginx/error.log
gunicorn -b "unix:/run/gunicorn.sock" main:application > /var/log/nginx/gunicorn_logs.txt &
GUNICORN=$!
nginx -g "daemon off;" > /var/log/nginx/nginx_additional_logs.txt &
NGINX=$!
tail -f /var/log/nginx/gunicorn_logs.txt /var/log/nginx/nginx_additional_logs.txt /var/log/nginx/access.log /var/log/nginx/error.log
kill $NGINX
kill $GUNICORN

FROM python:3.11-alpine

RUN apk add nginx zip

WORKDIR /app

COPY deploy/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY deploy /app/deploy
RUN mkdir -p /etc/nginx/sites-available/ /etc/nginx/sites-enabled/
RUN cp /app/deploy/nginx.conf /etc/nginx/
RUN cp /app/deploy/sites.conf /etc/nginx/sites-available/fileserver.conf
RUN ln -s /etc/nginx/sites-available/fileserver.conf /etc/nginx/sites-enabled/fileserver.conf

ENV USER=1000
RUN adduser --disabled-password --gecos "" --uid $USER -G www-data www-data
RUN mkdir -p /tmp/flask_sessions
RUN chown -R www-data:www-data /var/lib/nginx /var/log/nginx/ /run /tmp/flask_sessions

COPY cert /app/cert
COPY server /app/server
RUN chmod -R ugo+r /app
WORKDIR /app/server

USER www-data

EXPOSE 80
EXPOSE 443
CMD ["sh", "/app/deploy/start.sh"]

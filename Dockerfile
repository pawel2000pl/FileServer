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

ARG UID=1000
ARG GID=1000

ARG USERNAME=app

RUN set -eux; \
    if ! getent group "${GID}" >/dev/null 2>&1; then \
        addgroup -g "${GID}" "fileserver"; \
    fi; \
    \
    GROUP_NAME="$(getent group "${GID}" | cut -d: -f1)"; \
    \
    if ! id -u "fileserver" >/dev/null 2>&1; then \
        adduser -D -u "${UID}" -G "${GROUP_NAME}" "fileserver"; \
    fi


RUN mkdir -p /app/storage /app/storage/fileserver_home /app/storage/common /app/storage/sessions /app/storage/upload /app/storage/database
RUN chown -R fileserver:www-data /var/lib/nginx /var/log/nginx/ /run /app/storage
RUN chmod -R ug+rw,o-w /var/lib/nginx /var/log/nginx/ /run /app/storage

COPY cert /app/cert
RUN sh /app/deploy/placeholder_cert.sh
COPY server /app/server
RUN chmod -R ug+r /app /app/server /app/deploy /app/cert
WORKDIR /app/server

USER fileserver

EXPOSE 80
EXPOSE 443
CMD ["sh", "/app/deploy/start.sh"]

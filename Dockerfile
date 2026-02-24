FROM python:3.11-alpine

RUN apk add nginx

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /etc/nginx/sites-available/ /etc/nginx/sites-enabled/
RUN cp /app/deploy/nginx.conf /etc/nginx/
RUN cp /app/deploy/sites.conf /etc/nginx/sites-available/fileserver.conf
RUN ln -s /etc/nginx/sites-available/fileserver.conf /etc/nginx/sites-enabled/fileserver.conf

RUN chmod ugo+r /app
WORKDIR /app/server

ENV USER=1000

EXPOSE 80
EXPOSE 443
CMD ["sh", "/app/deploy/start.sh"]

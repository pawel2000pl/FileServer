#!/bin/sh

if ! [ -e '/app/cert/root.pem' ]
then
    echo "WARNING: generating temporary certificates for localhost"
    apk add --no-cache openssl
    cd '/app/cert'
    RUN openssl req -x509 -newkey rsa:4096 -nodes -out root.pem -keyout root-key.pem -days 365 -subj "/C=PL/ST=ExampleState/L=ExampleCity/O=ExampleCompany/CN=localhost"
    apk del openssl
fi

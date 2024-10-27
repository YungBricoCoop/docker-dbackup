FROM python:3.10-alpine

RUN apk update && apk add --no-cache \
  mysql-client \
  mariadb-connector-c \
  openssl \
  openssh-client \
  rm -rf /var/cache/apk/*

WORKDIR /dbackup

COPY src/. ./
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /dbackup/config /dbackup/storage

VOLUME /dbackup/config
VOLUME /dbackup/storage

ENTRYPOINT ["python3", "main.py"]

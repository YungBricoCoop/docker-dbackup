FROM python:3.10-alpine

RUN apk update && apk add --no-cache \
  mysql-client \
  mariadb-connector-c \
  openssl \
  openssh-client \
  bash \
  rm -rf /var/cache/apk/*

WORKDIR /dbackup

COPY src/. ./
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /dbackup/config /dbackup/storage

VOLUME /dbackup/config
VOLUME /dbackup/storage

#ENV DB_ID
#ENV DB_HOSTNAME
#ENV DB_PORT
#ENV DB_USERNAME
#ENV DB_PASSWORD
#ENV DB_DATABASE

#ENV HOST_ID
#ENV HOST_HOSTNAME
#ENV HOST_USERNAME
#ENV HOST_PASSWORD
#ENV HOST_PORT
#ENV HOST_PROTOCOL

#ENV NOTIFICATION_ID
#ENV NOTIFICATION_METHOD
#ENV DISCORD_WEBHOOK_URL
#ENV SMTP_SERVER
#ENV SMTP_PORT
#ENV SMTP_USER
#ENV SMTP_PASSWORD
#ENV SMTP_SENDER
#ENV SMTP_RECIPIENTS
#ENV SMTP_USE_TLS
#ENV SMTP_USE_SSL

ENTRYPOINT ["python3", "main.py"]

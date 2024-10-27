FROM python:3.10-alpine

RUN apk update && apk add --no-cache \
  mysql-client \
  mariadb-connector-c \
  openssl \
  openssh-client

WORKDIR /app

COPY src/. ./
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python3", "main.py"]

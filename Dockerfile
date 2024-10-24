FROM python:3.10-alpine

RUN apk update && apk add --no-cache \
  mysql-client \
  bash \
  xz \
  openssl


WORKDIR /app

COPY src/ ./
RUN pip install --no-cache-dir -r requirements.txt

# ENV vars
ENV MYSQL_HOST="localhost"
ENV MYSQL_PORT="3306"
ENV MYSQL_USER="root"
ENV MYSQL_PASSWORD=""
ENV MYSQL_DATABASE=""

ENV CRON_SCHEDULE="0 2 * * *"

# options: none, smtp, discord
ENV NOTIFICATION_METHOD="none" 
ENV SMTP_SERVER=""
ENV SMTP_PORT="587"
ENV SMTP_USER=""
ENV SMTP_PASSWORD=""
ENV SMTP_RECIPIENT=""
ENV DISCORD_WEBHOOK_URL=""

# options: volume, ssh, ftp
ENV BACKUP_METHOD="volume" 
ENV BACKUP_DESTINATION_PATH="/backup"
ENV SSH_HOST=""
ENV SSH_PORT="22"
ENV SSH_USER=""
ENV SSH_PASSWORD=""
ENV FTP_HOST=""
ENV FTP_PORT="21"
ENV FTP_USER=""
ENV FTP_PASSWORD=""

ENV MAX_BACKUP_FILES="30"

ENV SKIP_TABLES=""

ENV CONFIG_FILE="/config/backup.conf"

ENV ENCRYPTION_ENABLED="false"
ENV ENCRYPTION_PASSWORD=""

ENV COMPRESSION_ENABLED="true"

ENTRYPOINT ["python3", "main.py"]

# 🐋 docker-dbackup

A lightweight docker image for backing up databases, with options for local and remote storage, file encryption, and notification support on backup status.

With dbackup, you can:

- Dump your database (MySQL / MariaDB) to a file.
- Compress and/or encrypt the backup file.
- Store backups locally or on a remote host via SCP, SFTP, or FTP.
- Receive notifications on backup success or failure through Email or Discord.

## 🚀 Running dbackup

To run dbackup, you need to mount the configuration file and the storage directory to the container. Below is an example command to run the dbackup container:

```bash
docker run -d \
  -v /path/to/config.yaml:/dbackup/config/config.yaml \
  -v /path/to/storage:/dbackup/storage \
  -e TZ=Europe/Zurich \
  --name dbackup \
  yungbricocoop/dbackup:latest
```

Replace the timezone `Europe/Zurich` with your timezone. You can find a list of valid timezones [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

## 🛠️ Configuration

The configuration for dbackup is managed through a `YAML` file. Below is the structure of the configuration options, with examples for different use cases Each setting in **global_config** can be overridden by the settings in **backups**.

---

### Example Configurations

**Basic Local Backup** : This configuration includes a basic local backup without compression or encryption.

```yaml
global_config:
  compression_enabled: false
  encryption_enabled: false

db_connections:
  - id: "local-db"
    hostname: "127.0.0.1"
    username: "root"
    password: "example_password"
    database: "mydatabase"

backups:
  - id: "basic-local-backup"
    db_connection_id: "local-db"
    local: true
    path: "/dbackup/storage/"
    schedule: "0 0 * * *" # Daily backup at midnight
```

</br>

**Remote Backup with Compression and Encryption** : This configuration includes encryption and compression for secure storage on a remote server via SCP.

```yaml
global_config:
  encryption_enabled: true
  encryption_password: "super_secret"
  compression_enabled: true

db_connections:
  - id: "remote-db"
    hostname: "192.168.1.10"
    username: "user"
    password: "db_password"
    database: "important_db"

hosts:
  - id: "backup-server"
    hostname: "backup.example.com"
    username: "backup_user"
    ssh_key: "/path/to/ssh_key"
    port: 22
    protocol: "scp"

backups:
  - id: "encrypted-remote-backup"
    db_connection_id: "remote-db"
    host_id: "backup-server"
    path: "/remote-path/"
    filename: "backup-{date}.sql"
    schedule: "30 2 * * *" # Backup at 2:30 AM every day
```

</br>

**Local Backup with Notification on Failure** : In this configuration, the backup will store locally and send notifications via Email and Discord on failure.

```yaml
global_config:
  compression_enabled: true
  encryption_enabled: false

db_connections:
  - id: "critical-db"
    hostname: "10.0.0.5"
    username: "admin"
    password: "password123"
    database: "critical_db"

notifications:
  - id: "email-fail-notify"
    method: "email"

    smtp_server: "smtp.example.com"
    smtp_port: 587
    smtp_user: "user@example.com"
    smtp_password: "smtp_password"
    smtp_sender: "user@example.com"
    smtp_recipients: ["admin@example.com"]
    smtp_use_tls: true
    smtp_use_ssl: false
  - id: "discord-notify"
    method: "discord"
    webhook_url: "https://discord.com/api/webhooks/1234567890/abcdefg"

backups:
  - id: "local-critical-backup"
    db_connection_id: "critical-db"
    local: true
    path: "/dbackup/storage/"
    notify_on_success: false
    notify_on_fail: true
    notification_ids: ["email-fail-notify", "discord-notify"]
    schedule: "0 0 * * SUN" # Weekly backup at midnight on Sundays
```

## 📜 Logs

By default, the logs are stored in the `/dbackup/storage/logs` directory inside the container.

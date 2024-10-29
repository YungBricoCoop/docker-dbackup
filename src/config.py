import yaml
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError
from typing import List, Optional
from croniter import croniter
from loguru import logger
from enum import Enum


class NotificationMethod(str, Enum):
    EMAIL = "email"
    DISCORD = "discord"


class Protocol(str, Enum):
    SCP = "scp"
    SFTP = "sftp"
    FTP = "ftp"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DBConnection(BaseModel):
    id: str
    hostname: str
    port: int = Field(default=3306)
    username: str
    password: str
    database: str


class Host(BaseModel):
    id: str
    hostname: str
    username: str
    password: Optional[str] = None
    ssh_key: Optional[str] = None
    port: int
    protocol: Protocol

    @model_validator(mode="after")
    def validate_host(cls, model):
        if model.protocol == Protocol.FTP and not model.password:
            raise ValueError(f"Password must be specified for FTP protocol.")

        if model.protocol in [Protocol.SCP, Protocol.SFTP]:
            if not model.password and not model.ssh_key:
                raise ValueError(
                    "Either password or SSH key must be specified for SCP/SFTP protocol."
                )
            if model.password and model.ssh_key:
                raise ValueError(
                    "Only one of password or SSH key can be used for SCP/SFTP protocol."
                )
        return model


class Notification(BaseModel):
    id: str
    method: NotificationMethod
    notify_on_fail: bool = Field(default=True)
    notify_on_success: bool = Field(default=False)
    webhook_url: Optional[str] = None
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = Field(default=587)
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_sender: Optional[str] = None
    smtp_recipients: Optional[List[str]] = Field(default_factory=list)
    smtp_use_tls: Optional[bool] = Field(default=True)
    smtp_use_ssl: Optional[bool] = Field(default=False)

    @model_validator(mode="after")
    def validate_notification(cls, model):
        if model.method == NotificationMethod.EMAIL:
            required_fields = [
                "smtp_server",
                "smtp_port",
                "smtp_user",
                "smtp_password",
                "smtp_sender",
                "smtp_recipients",
            ]
            for field_name in required_fields:
                value = getattr(model, field_name)
                if not value:
                    raise ValueError(
                        f"Field '{field_name}' is required when method is 'email'."
                    )
        elif model.method == NotificationMethod.DISCORD:
            if not model.webhook_url:
                raise ValueError(
                    "Field 'webhook_url' is required when method is 'discord'."
                )
        return model


class Backup(BaseModel):
    id: str
    host_id: Optional[str] = None
    db_connection_id: str
    notification_ids: Optional[List[str]] = None
    host_obj: Optional[Host] = None
    db_connection_obj: Optional[DBConnection] = None
    notification_objs: Optional[List[Notification]] = None
    local: bool = Field(default=False)
    path: str  # path to the backup directory (remote or local)
    filename: Optional[str] = None
    date_format: Optional[str] = None
    encryption_enabled: Optional[bool] = None
    encryption_password: Optional[str] = None
    compression_enabled: Optional[bool] = None
    skip_tables: Optional[List[str]] = None
    dump_options: Optional[List[str]] = None
    max_backup_files: Optional[int] = None
    schedule: Optional[str] = None

    @field_validator("host_id")
    def validate_host_id(cls, value, info):
        local = info.data.get("local")
        if not local and not value:
            raise ValueError(
                f"Either 'host_id' or 'local' must be specified for backup '{info.data.get('id')}'."
            )
        if local and value:
            raise ValueError(
                f"Only one of 'host_id' or 'local' can be specified for backup '{info.data.get('id')}'."
            )
        return value

    @field_validator("schedule")
    def validate_schedule(cls, value):
        if value and not croniter.is_valid(value):
            raise ValueError(f"Invalid cron syntax: '{value}'.")
        return value


class GlobalConfig(BaseModel):
    date_format: Optional[str] = Field(default="%Y-%m-%d_%H-%M-%S")
    encryption_enabled: Optional[bool] = Field(default=False)
    encryption_password: Optional[str] = Field(default="")
    compression_enabled: Optional[bool] = Field(default=True)
    skip_tables: Optional[List[str]] = Field(default_factory=list)
    dump_options: Optional[List[str]] = Field(default_factory=list)
    max_backup_files: Optional[int] = Field(default=100)
    schedule: Optional[str] = Field(default="0 0 * * *")
    notification_ids: Optional[List[str]] = Field(default_factory=list)

    @field_validator("schedule")
    def validate_schedule(cls, value):
        if value and not croniter.is_valid(value):
            raise ValueError(f"Invalid cron syntax: '{value}'.")
        return value


class Log(BaseModel):
    level: LogLevel = Field(default=LogLevel.INFO)
    filename: Optional[str] = Field(default="/dbackup/storage/logs/dbackup.log")
    rotation_interval: Optional[str] = Field(default="1 day")
    retention_period: Optional[str] = Field(default="7 days")
    format: Optional[str] = Field(
        default="<green>{time:DD.MM.YYYY HH:mm:ss.SSS}</green> | <level>{level}</level> | <level>{message}</level>"
    )


class Config(BaseModel):
    global_config: GlobalConfig
    db_connections: List[DBConnection]
    hosts: Optional[List[Host]] = Field(default_factory=list)
    backups: List[Backup]
    notifications: Optional[List[Notification]] = Field(default_factory=list)
    log: Optional[Log] = Field(default_factory=Log)

    @model_validator(mode="after")
    def validate_backups(cls, model):
        # check for unique ids in db_connections
        db_ids = [db.id for db in model.db_connections]
        if len(db_ids) != len(set(db_ids)):
            raise ValueError("Duplicate ids found in 'db_connections'.")

        # check for unique ids in hosts
        host_ids = [host.id for host in model.hosts]
        if len(host_ids) != len(set(host_ids)):
            raise ValueError("Duplicate ids found in 'hosts'.")

        # check for unique ids in backups
        backup_ids = [backup.id for backup in model.backups]
        if len(backup_ids) != len(set(backup_ids)):
            raise ValueError("Duplicate ids found in 'backups'.")

        # check for unique ids in notifications
        notification_ids_list = [
            notification.id for notification in model.notifications
        ]
        if len(notification_ids_list) != len(set(notification_ids_list)):
            raise ValueError("Duplicate ids found in 'notifications'.")

        # check db_connection_id and host_id references in backup
        db_connection_id_set = set(db_ids)
        host_id_set = set(host_ids)

        for backup in model.backups:
            if not backup.local and backup.host_id not in host_id_set:
                raise ValueError(
                    f"Backup '{backup.id}': host_id '{backup.host_id}' is not defined in hosts."
                )

            if backup.db_connection_id not in db_connection_id_set:
                raise ValueError(
                    f"Backup '{backup.id}': db_connection_id '{backup.db_connection_id}' is not defined in db_connections."
                )

            # set defaults from global_config if not set in backup
            for field_name in [
                "date_format",
                "encryption_enabled",
                "encryption_password",
                "compression_enabled",
                "skip_tables",
                "dump_options",
                "max_backup_files",
                "schedule",
                "notification_ids",
            ]:
                if getattr(backup, field_name) is None:
                    setattr(
                        backup, field_name, getattr(model.global_config, field_name)
                    )

            # set host_obj, db_connection_obj, and notification_objs
            backup.host_obj = next(
                (host for host in model.hosts if host.id == backup.host_id), None
            )
            backup.db_connection_obj = next(
                (db for db in model.db_connections if db.id == backup.db_connection_id),
                None,
            )

            backup.notification_objs = [
                notification
                for notification in model.notifications
                if notification.id in (backup.notification_ids or [])
            ]

        return model


def get_config(config_file) -> Optional[Config]:
    config = None
    try:
        with open(config_file, "r") as file:
            config_data = yaml.safe_load(file)
        config = Config(**config_data)
    except FileNotFoundError as e:
        logger.error(f"Config file not found: {e}")
    except ValidationError as e:
        logger.error(f"Config validation failed: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    return config

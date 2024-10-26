import yaml
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError
from typing import List, Optional
from croniter import croniter
from loguru import logger


class DBConnection(BaseModel):
    name: str
    host: str
    port: int = Field(default=3306)
    username: str
    password: str
    database: str


class Host(BaseModel):
    name: str
    host: str
    username: str
    password: Optional[str] = None
    private_ssh_key: Optional[str] = None
    port: int
    protocol: str = Field(pattern="scp|sftp|ftp")

    @model_validator(mode="after")
    def validate_host(cls, model):
        if model.protocol == "ftp" and not model.password:
            raise ValueError(f"Password must be specified for FTP protocol.")

        if model.protocol in ["scp", "sftp"]:
            if not model.password and not model.private_ssh_key:
                raise ValueError(
                    "Either password or private SSH key must be specified for SCP/SFTP protocol."
                )
            if model.password and model.private_ssh_key:
                raise ValueError(
                    "Either password or private SSH key can be used for SCP/SFTP protocol."
                )
        return model


class Backup(BaseModel):
    name: str
    host: Optional[str] = None
    local: bool = Field(default=False)
    path: str  # path to the backup directory (remote or local)
    db_connection: str
    filename: str = None
    encryption_enabled: Optional[bool] = None
    encryption_password: Optional[str] = None
    compression_enabled: Optional[bool] = None
    skip_tables: Optional[str] = None
    retention_period: Optional[str] = None
    schedule: Optional[str] = None
    host_obj: Optional[Host] = None
    db_connection_obj: Optional[DBConnection] = None

    @field_validator("host")
    def validate_host(cls, value, info):
        local = info.data.get("local")
        if not local and not value:
            raise ValueError(
                f"Either 'host' or 'local' must be specified for backup '{info.data.get('name')}'"
            )
        if local and value:
            raise ValueError(
                f"Only one of 'host' or 'local' can be specified for backup '{info.data.get('name')}'"
            )
        return value

    @field_validator("schedule")
    def validate_schedule(cls, value):
        if value and not croniter.is_valid(value):
            raise ValueError(f"Invalid cron syntax: '{value}'")
        return value


class Notification(BaseModel):
    method: str = Field(default="email", pattern="email|discord")
    notify_on_fail: bool = Field(default=True)
    notify_on_success: bool = Field(default=False)
    smtp_server: Optional[str] = Field(default="")
    smtp_port: Optional[int] = Field(default=587)
    smtp_user: Optional[str] = Field(default="")
    smtp_password: Optional[str] = Field(default="")
    smtp_recipient: Optional[str] = Field(default="")


class GlobalConfig(BaseModel):
    encryption_enabled: Optional[bool] = Field(default=False)
    encryption_password: Optional[str] = Field(default="")
    compression_enabled: Optional[bool] = Field(default=True)
    skip_tables: Optional[str] = Field(default="")
    retention_period: Optional[str] = Field(default="7 days")
    schedule: Optional[str] = Field(default="0 0 * * *")

    @field_validator("schedule")
    def validate_schedule(cls, value):
        if value and not croniter.is_valid(value):
            raise ValueError(f"Invalid cron syntax: '{value}'")
        return value


class Log(BaseModel):
    level: str = Field(default="INFO", pattern="DEBUG|INFO|WARNING|ERROR|CRITICAL")
    file: Optional[str] = Field(default="/var/log/backup.log")
    rotation_interval: Optional[str] = Field(default="1 day")
    retention_period: Optional[str] = Field(default="7 days")
    format: Optional[str] = Field(
        default="<green>{time:DD.MM.YYYY HH:mm:ss.SSS}</green> | <level>{level}</level> | <level>{message}</level>"
    )


class Config(BaseModel):
    global_config: GlobalConfig
    db_connections: List[DBConnection]
    hosts: List[Host]
    backup: List[Backup]
    notifications: Optional[List[Notification]] = Field(default=[])
    log: Optional[Log] = Field(default=Log())

    @model_validator(mode="after")
    def validate_backups(cls, model):
        # check for unique names in db_connections
        db_names = [db.name for db in model.db_connections]
        if len(db_names) != len(set(db_names)):
            raise ValueError("Duplicate names found in 'db_connections'")

        # check for unique names in hosts
        host_names = [host.name for host in model.hosts]
        if len(host_names) != len(set(host_names)):
            raise ValueError("Duplicate names found in 'hosts'")

        # check for unique names in backup
        backup_names = [backup.name for backup in model.backup]
        if len(backup_names) != len(set(backup_names)):
            raise ValueError("Duplicate names found in 'backup'")

        # check db_connection and host references in backup
        db_connection_names = set(db_names)
        host_name_set = set(host_names)

        for backup in model.backup:
            if not backup.local and backup.host not in host_name_set:
                raise ValueError(
                    f"Backup '{backup.name}': host '{backup.host}' is not defined in hosts, if you want to use a local backup, set 'local: true'"
                )

            if backup.db_connection not in db_connection_names:
                raise ValueError(
                    f"Backup '{backup.name}': db_connection '{backup.db_connection}' is not defined in db_connections"
                )

            # set host_obj and db_connection_obj
            backup.host_obj = next(
                (host for host in model.hosts if host.name == backup.host), None
            )
            backup.db_connection_obj = next(
                (db for db in model.db_connections if db.name == backup.db_connection),
                None,
            )

            # set defaults from global_config if not set in backup
            for field in [
                "encryption_enabled",
                "encryption_password",
                "compression_enabled",
                "skip_tables",
                "retention_period",
                "schedule",
            ]:
                if getattr(backup, field) is None:
                    setattr(backup, field, getattr(model.global_config, field))
        return model


def get_config(config_file) -> Config:
    config = None
    try:
        with open(config_file, "r") as file:
            config_data = yaml.safe_load(file)
        config = Config(**config_data)
    except FileNotFoundError as e:
        logger.error(f"Config file not found: {e}")
    except ValidationError as e:
        logger.error(f"Config validation failed: {e}")
    return config

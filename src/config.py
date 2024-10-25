import yaml
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from croniter import croniter

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
    password: str

class Backup(BaseModel):
    name: str
    protocol: str = Field(pattern="ssh|sftp|ftp|local")
    host: Optional[str] = None
    path: str  # path to the backup directory (remote or local)
    port: Optional[int] = None
    db_connection: str
    filename: str = None
    encryption_enabled: Optional[bool] = None
    encryption_password: Optional[str] = None
    compression_enabled: Optional[bool] = None
    skip_tables: Optional[str] = None
    retention_period: Optional[str] = None
    schedule: Optional[str] = None

    @field_validator('host')
    def validate_host(cls, value, info):
        if info.data.get('protocol') != 'local' and not value:
            raise ValueError(
                f"Host must be specified for protocol '{info.data['protocol']}'"
            )
        return value

    @field_validator('port')
    def validate_port(cls, value, info):
        if info.data.get('protocol') != 'local' and not value:
            raise ValueError(
                f"Port must be specified for protocol '{info.data['protocol']}'"
            )
        return value

    @field_validator('schedule')
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

    @field_validator('schedule')
    def validate_schedule(cls, value):
        if value and not croniter.is_valid(value):
            raise ValueError(f"Invalid cron syntax: '{value}'")
        return value
    
class Log(BaseModel):
    level: str = Field(default="INFO", pattern="DEBUG|INFO|WARNING|ERROR|CRITICAL")
    file: Optional[str] = Field(default="/var/log/backup.log")
    rotation_interval: Optional[str] = Field(default="1 day")
    retention_period: Optional[str] = Field(default="7 days")


class Config(BaseModel):
    global_config: GlobalConfig 
    db_connections: List[DBConnection]
    hosts: List[Host]
    backup: List[Backup]
    notifications: Optional[List[Notification]] = Field(default=[])
    log: Optional[Log] = Field(default=Log())

    @model_validator(mode='after')
    def validate_backups(cls, model):
        db_connection_names = {db.name for db in model.db_connections}
        host_names = {host.name for host in model.hosts}

        for backup in model.backup:
            if backup.db_connection not in db_connection_names:
                raise ValueError(
                    f"Backup '{backup.name}': db_connection '{backup.db_connection}' is not defined in db_connections"
                )

            if backup.protocol != 'local':
                if not backup.host:
                    raise ValueError(
                        f"Backup '{backup.name}': host must be specified for protocol '{backup.protocol}'"
                    )
                if backup.host not in host_names:
                    raise ValueError(
                        f"Backup '{backup.name}': host '{backup.host}' is not defined in hosts"
                    )
            
            # set defaults from global_config if not set in backup
            for field in ['encryption_enabled', 'encryption_password', 'compression_enabled', 'skip_tables', 'retention_period', 'schedule']:
                if getattr(backup, field) is None:
                    setattr(backup, field, getattr(model.global_config, field))
        return model



def get_config(config_file) -> Config :
    with open(config_file, 'r') as file:
        config_data = yaml.safe_load(file)

    config = Config(**config_data)
    return config
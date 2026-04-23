from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    db_type: str
    host: str
    port: int
    database: str
    username: str
    password: str


@dataclass
class FieldInfo:
    iof_id: int
    iof_engname: str
    iof_chiname: str

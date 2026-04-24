from dataclasses import dataclass
from typing import Any, Dict


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


@dataclass
class ProtocolOption:
    obj_guid: str
    sys_id: str
    data: Dict[str, Any]

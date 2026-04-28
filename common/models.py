from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class DatabaseConfig:
    """数据库连接配置，对应 config/database.yml。"""

    db_type: str
    host: str
    port: int
    database: str
    username: str
    password: str


@dataclass
class FieldInfo:
    """协议字段元数据，用于生成 BCP 记录和 ZIP 内 XML。"""

    iof_id: int
    iof_keyname: str
    iof_engname: str
    iof_chiname: str


@dataclass
class ProtocolOption:
    """协议查询返回的一条候选协议记录。"""

    obj_guid: str
    sys_id: str
    data: Dict[str, Any]

from dataclasses import dataclass
from pathlib import Path

from common.database import build_engine
from common.fake_data import FakeDataBuilder
from common.file_reader import read_sql_blocks, read_yaml
from common.models import DatabaseConfig
from common.paths import get_resource_dir


@dataclass
class RuntimeContext:
    """功能入口共用的运行时依赖。"""

    resource_dir: Path
    engine: object
    builder: FakeDataBuilder
    protocol_sql: str
    field_sql: str


def create_runtime_context() -> RuntimeContext:
    """读取配置文件，并创建数据库和假数据生成相关对象。"""
    resource_dir = get_resource_dir()
    db_config = DatabaseConfig(**read_yaml(resource_dir / "config" / "database.yml"))
    protocol_sql, field_sql = read_sql_blocks(resource_dir / "sql" / "fieId.sql")
    fake_rules = read_yaml(resource_dir / "config" / "fake.yml")

    engine = build_engine(db_config)
    return RuntimeContext(
        resource_dir=resource_dir,
        engine=engine,
        builder=FakeDataBuilder(fake_rules, engine=engine),
        protocol_sql=protocol_sql,
        field_sql=field_sql,
    )

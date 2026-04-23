import sys
from pathlib import Path

from app.bcp_writer import write_bcp
from app.database import build_engine, query_fields, query_sys_id
from app.fake_data import FakeDataBuilder
from app.file_reader import read_sql_blocks, read_yaml
from app.models import DatabaseConfig


def get_resource_dir() -> Path:
    if getattr(sys, "frozen", False):
        external_dir = Path(sys.executable).resolve().parent
        if (external_dir / "sql").exists() and (external_dir / "fakedata").exists():
            return external_dir
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent.parent


def get_output_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "output"
    return Path(__file__).resolve().parent.parent / "output"


def main() -> None:
    resource_dir = get_resource_dir()
    protocol_name = input("请输入协议英文名: ").strip()
    if not protocol_name:
        raise ValueError("协议英文名不能为空。")

    db_config = DatabaseConfig(**read_yaml(resource_dir / "sql" / "database.yml"))
    field_sql, sys_sql = read_sql_blocks(resource_dir / "sql" / "fieId.sql")
    fake_rules = read_yaml(resource_dir / "fakedata" / "fake.yml")

    engine = build_engine(db_config)
    fields = query_fields(engine, field_sql, protocol_name)
    sys_id = query_sys_id(engine, sys_sql, protocol_name)
    record = FakeDataBuilder(fake_rules).build_record(fields)

    output_path = write_bcp(get_output_dir(), sys_id, protocol_name, record)
    print(f"生成成功: {output_path}")

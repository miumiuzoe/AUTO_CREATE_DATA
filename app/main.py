import sys
from pathlib import Path
from typing import List

from app.bcp_writer import write_bcp
from app.database import build_engine, query_fields, query_protocols
from app.fake_data import FakeDataBuilder
from app.file_reader import read_sql_blocks, read_yaml
from app.models import DatabaseConfig, ProtocolOption


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


def choose_protocol(protocol_name: str, protocols: List[ProtocolOption]) -> ProtocolOption:
    if len(protocols) == 1:
        return protocols[0]

    print(f"协议 {protocol_name} 查询到多个结果，请选择要生成数据的目标协议：")
    for index, protocol in enumerate(protocols, start=1):
        print(f"{index}. {_format_protocol(protocol)}")

    while True:
        raw_value = input("请输入序号: ").strip()
        if not raw_value.isdigit():
            print("输入无效，请输入数字序号。")
            continue

        selected_index = int(raw_value)
        if 1 <= selected_index <= len(protocols):
            return protocols[selected_index - 1]

        print("序号超出范围，请重新输入。")


def _format_protocol(protocol: ProtocolOption) -> str:
    preferred_keys = ["OBJ_GUID", "SYS_ID", "OBJ_ENGNAME", "OBJ_ENG", "OBJ_CHINAME", "OBJ_CHI", "OBJ_NAME"]
    ordered_items = []
    used_keys = set()

    for key in preferred_keys:
        if key in protocol.data:
            ordered_items.append((key, protocol.data[key]))
            used_keys.add(key)

    for key, value in protocol.data.items():
        if key not in used_keys:
            ordered_items.append((key, value))

    return ", ".join(f"{key}={value}" for key, value in ordered_items)


def _parse_protocol_names(raw_protocol_names: str) -> List[str]:
    protocol_names = [item.strip() for item in raw_protocol_names.split(",")]
    protocol_names = [item for item in protocol_names if item]
    if not protocol_names:
        raise ValueError("协议英文名不能为空。")
    return protocol_names


def main() -> None:
    resource_dir = get_resource_dir()
    raw_protocol_names = input("请输入协议英文名，多个协议用英文逗号分隔: ").strip()
    protocol_names = _parse_protocol_names(raw_protocol_names)

    db_config = DatabaseConfig(**read_yaml(resource_dir / "sql" / "database.yml"))
    protocol_sql, field_sql = read_sql_blocks(resource_dir / "sql" / "fieId.sql")
    fake_rules = read_yaml(resource_dir / "fakedata" / "fake.yml")

    engine = build_engine(db_config)
    builder = FakeDataBuilder(fake_rules, engine=engine)

    for protocol_name in protocol_names:
        selected_protocol = choose_protocol(
            protocol_name,
            query_protocols(engine, protocol_sql, protocol_name),
        )
        fields = query_fields(engine, field_sql, selected_protocol.obj_guid, protocol_name)
        record = builder.build_record(fields)
        output_path = write_bcp(get_output_dir(), selected_protocol.sys_id, protocol_name, record)
        print(f"{protocol_name} 生成成功: {output_path}")

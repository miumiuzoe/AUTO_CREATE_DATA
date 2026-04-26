from pathlib import Path
from typing import Callable, List, Tuple

from app.bcp_writer import build_bcp_name
from app.database import build_engine, query_fields, query_protocols
from app.fake_data import FakeDataBuilder
from app.file_reader import read_sql_blocks, read_yaml
from app.main import choose_protocol, get_output_dir, get_resource_dir
from app.models import DatabaseConfig, FieldInfo


SIZE_MODE = "1"
COUNT_MODE = "2"


def main() -> None:
    resource_dir = get_resource_dir()
    protocol_name = _read_protocol_name()
    batch_mode = _read_batch_mode()
    limit_value = _read_limit_value(batch_mode)
    file_count = _read_positive_int("请输入要生成的文件个数: ")

    db_config = DatabaseConfig(**read_yaml(resource_dir / "sql" / "database.yml"))
    protocol_sql, field_sql = read_sql_blocks(resource_dir / "sql" / "fieId.sql")
    fake_rules = read_yaml(resource_dir / "fakedata" / "fake.yml")

    engine = build_engine(db_config)
    builder = FakeDataBuilder(fake_rules, engine=engine)
    selected_protocol = choose_protocol(
        protocol_name,
        query_protocols(engine, protocol_sql, protocol_name),
    )
    fields = query_fields(engine, field_sql, selected_protocol.obj_guid, protocol_name)

    if batch_mode == SIZE_MODE:
        file_paths = _generate_by_size(
            get_output_dir(),
            selected_protocol.sys_id,
            protocol_name,
            fields,
            builder,
            limit_value,
            file_count,
        )
        print(f"已按单文件大小 {limit_value} MB 生成 {len(file_paths)} 个文件。")
    else:
        file_paths = _generate_by_count(
            get_output_dir(),
            selected_protocol.sys_id,
            protocol_name,
            fields,
            builder,
            limit_value,
            file_count,
        )
        print(f"已按单文件 {limit_value} 条记录生成 {len(file_paths)} 个文件。")

    for path in file_paths:
        print(path)


def _read_protocol_name() -> str:
    protocol_name = input("请输入协议英文名: ").strip()
    if not protocol_name:
        raise ValueError("协议英文名不能为空。")
    return protocol_name


def _read_batch_mode() -> str:
    print("请选择批量生成方式：")
    print("1. 按单个文件大小限制")
    print("2. 按单个文件记录条数限制")

    while True:
        mode = input("请输入序号(1/2): ").strip()
        if mode in (SIZE_MODE, COUNT_MODE):
            return mode
        print("输入无效，请输入 1 或 2。")


def _read_limit_value(batch_mode: str) -> int:
    if batch_mode == SIZE_MODE:
        return _read_positive_int("请输入单个文件大小限制(MB): ")
    return _read_positive_int("请输入单个文件记录条数限制: ")


def _read_positive_int(prompt: str) -> int:
    while True:
        raw_value = input(prompt).strip()
        if raw_value.isdigit() and int(raw_value) > 0:
            return int(raw_value)
        print("输入无效，请输入大于 0 的整数。")


def _generate_by_size(
    output_dir: Path,
    sys_id: str,
    protocol_name: str,
    fields: List[FieldInfo],
    builder: FakeDataBuilder,
    size_limit_mb: int,
    file_count: int,
) -> List[Path]:
    size_limit_bytes = size_limit_mb * 1024 * 1024
    return _generate_files(
        output_dir,
        sys_id,
        protocol_name,
        file_count,
        lambda target: _write_records_until_size(target, fields, builder, size_limit_bytes),
    )


def _generate_by_count(
    output_dir: Path,
    sys_id: str,
    protocol_name: str,
    fields: List[FieldInfo],
    builder: FakeDataBuilder,
    record_limit: int,
    file_count: int,
) -> List[Path]:
    return _generate_files(
        output_dir,
        sys_id,
        protocol_name,
        file_count,
        lambda target: _write_records_by_count(target, fields, builder, record_limit),
    )


def _generate_files(
    output_dir: Path,
    sys_id: str,
    protocol_name: str,
    file_count: int,
    writer: Callable[[Path], Tuple[int, int]],
) -> List[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_paths = []

    for index in range(file_count):
        target = output_dir / build_bcp_name(sys_id, protocol_name)
        record_count, file_size = writer(target)
        file_paths.append(target)
        file_size_mb = file_size / (1024 * 1024)
        print(
            f"[{index + 1}/{file_count}] 生成成功: {target}，记录数={record_count}，"
            f"文件大小={file_size_mb:.2f} MB（{file_size} 字节）"
        )

    return file_paths


def _write_records_until_size(
    target: Path,
    fields: List[FieldInfo],
    builder: FakeDataBuilder,
    size_limit_bytes: int,
) -> Tuple[int, int]:
    bytes_written = 0
    record_count = 0

    with target.open("w", encoding="utf-8", newline="") as file_obj:
        while bytes_written < size_limit_bytes or record_count == 0:
            line = builder.build_record(fields) + "\n"
            line_bytes = line.encode("utf-8")

            if record_count > 0 and bytes_written + len(line_bytes) > size_limit_bytes:
                break

            file_obj.write(line)
            bytes_written += len(line_bytes)
            record_count += 1

    return record_count, bytes_written


def _write_records_by_count(
    target: Path,
    fields: List[FieldInfo],
    builder: FakeDataBuilder,
    record_limit: int,
) -> Tuple[int, int]:
    bytes_written = 0

    with target.open("w", encoding="utf-8", newline="") as file_obj:
        for _ in range(record_limit):
            line = builder.build_record(fields) + "\n"
            file_obj.write(line)
            bytes_written += len(line.encode("utf-8"))

    return record_limit, bytes_written

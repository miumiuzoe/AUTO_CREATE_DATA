from common.bcp_file import build_bcp_name
from common.database import query_fields, query_protocols
from common.paths import get_output_dir
from common.protocols import choose_protocol, parse_protocol_names
from common.runtime import create_runtime_context
from features.zip_package.zip_writer import write_zip_package


def main() -> None:
    """执行 ZIP 压缩包生成的交互流程。"""
    raw_protocol_names = input("请输入协议英文名，多个协议用英文逗号分隔: ").strip()
    protocol_names = parse_protocol_names(raw_protocol_names)
    context = create_runtime_context()

    for protocol_name in protocol_names:
        selected_protocol = choose_protocol(
            protocol_name,
            query_protocols(context.engine, context.protocol_sql, protocol_name),
        )
        fields = query_fields(context.engine, context.field_sql, selected_protocol.obj_guid, protocol_name)
        record = context.builder.build_record(fields)
        bcp_file_name = build_bcp_name(selected_protocol.sys_id, protocol_name)
        zip_path = write_zip_package(
            get_output_dir(),
            context.resource_dir / "template" / "zip.xml",
            protocol_name,
            selected_protocol.sys_id,
            bcp_file_name,
            record,
            fields,
        )
        print(f"{protocol_name} ZIP 生成成功: {zip_path}")

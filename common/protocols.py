from typing import List

from common.models import ProtocolOption


def parse_protocol_names(raw_protocol_names: str) -> List[str]:
    """解析用户输入的英文逗号分隔协议英文名。"""
    protocol_names = [item.strip() for item in raw_protocol_names.split(",")]
    protocol_names = [item for item in protocol_names if item]
    if not protocol_names:
        raise ValueError("协议英文名不能为空。")
    return protocol_names


def choose_protocol(protocol_name: str, protocols: List[ProtocolOption]) -> ProtocolOption:
    """从协议候选记录中选择一个，存在多条时要求用户输入序号。"""
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
    """将协议候选记录格式化为交互展示文本。"""
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

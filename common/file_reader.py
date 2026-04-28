from pathlib import Path
import re
from typing import Tuple

import yaml


def read_text(path: Path) -> str:
    """按项目支持的编码读取文本文件。"""
    for encoding in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"无法识别文件编码: {path}")


def read_yaml(path: Path) -> dict:
    """读取 YAML 文件，并要求顶层内容是字典。"""
    data = yaml.safe_load(read_text(path)) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML 文件顶层内容必须是字典: {path}")
    return data


def read_sql_blocks(path: Path) -> Tuple[str, str]:
    """从 SQL 配置文件中读取前两段可执行 SQL。"""
    sql_text = read_text(path)
    sql_text = re.sub(r"/\*.*?\*/", "", sql_text, flags=re.S)

    lines = []
    for raw_line in sql_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("--"):
            continue
        lines.append(raw_line)

    blocks = [block.strip() for block in "\n".join(lines).split(";") if block.strip()]
    if len(blocks) < 2:
        raise ValueError("sql/fieId.sql 至少需要包含两段 SQL。")

    return blocks[0], blocks[1]

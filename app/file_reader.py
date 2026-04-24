from pathlib import Path
import re
from typing import Tuple

import yaml


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"无法识别文件编码: {path}")


def read_yaml(path: Path) -> dict:
    data = yaml.safe_load(read_text(path)) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML 文件内容格式不正确: {path}")
    return data


def read_sql_blocks(path: Path) -> Tuple[str, str]:
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
        raise ValueError("sql/fieId.sql 需要包含两段 SQL。")

    return blocks[0], blocks[1]

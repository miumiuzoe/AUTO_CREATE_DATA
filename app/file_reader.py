from pathlib import Path
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
    blocks = []
    current = []

    for raw_line in read_text(path).splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue
        if line.startswith("--"):
            # 注释行也视为 SQL 段落分隔，避免两段 SQL 之间没有空行时被拼在一起。
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue
        current.append(raw_line.rstrip(";"))

    if current:
        blocks.append("\n".join(current).strip())

    if len(blocks) < 2:
        raise ValueError("sql/fieId.sql 需要包含两段 SQL。")

    return blocks[0], blocks[1]

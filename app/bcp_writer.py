import random
import time
from pathlib import Path


def write_bcp(output_dir: Path, sys_id: str, protocol_name: str, content: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_name = build_bcp_name(sys_id, protocol_name)
    target = output_dir / file_name
    target.write_text(content + "\n", encoding="utf-8")
    return target


def build_bcp_name(sys_id: str, protocol_name: str) -> str:
    timestamp = str(int(time.time()))
    random_code = random.randint(10000, 99999)
    return f"{sys_id}-310000-{timestamp}-{random_code}-{protocol_name}-0.bcp"

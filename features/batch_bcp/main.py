import time
from pathlib import Path

from common.paths import get_output_dir
from faker import Faker


# 输出目录。设置为 None 时写入项目默认 output 目录。
OUTPUT_DIR = None

# 每个文件生成的数据条数。
ROWS_PER_FILE = 100

# 需要生成的文件数量。
FILE_COUNT = 1


faker = Faker("zh_CN")


def build_record() -> str:
    """自定义每条数据的内容，字段之间使用 Tab 分隔。"""
    data = f"330300\t程波\t11494878168\t{faker.phone_number()}\t12351"
    return data


def build_file_name(sequence: int, curday: str, timestamp: str) -> str:
    """自定义输出文件名，sequence 从 00000 开始递增。"""
    x = f"{sequence:05d}"
    file_name = f"501-330000-{curday}-{timestamp}-{x}.bcp"
    return file_name


def main() -> None:
    """批量生成自定义的 Tab 分隔 BCP 类数据文件。"""
    _validate_config()
    output_dir = Path(OUTPUT_DIR) if OUTPUT_DIR else get_output_dir()
    curday = time.strftime("%Y%m%d")
    timestamp = str(int(time.time()))

    for sequence in range(FILE_COUNT):
        file_name = build_file_name(sequence, curday, timestamp)
        records = [build_record() for _ in range(ROWS_PER_FILE)]
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / file_name
        output_path.write_text("\n".join(records) + "\n", encoding="utf-8")
        print(f"批量文件生成成功({sequence + 1}/{FILE_COUNT}): {output_path}")


def _validate_config() -> None:
    if ROWS_PER_FILE <= 0:
        raise ValueError("ROWS_PER_FILE 必须大于 0")
    if FILE_COUNT <= 0:
        raise ValueError("FILE_COUNT 必须大于 0")

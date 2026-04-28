import sys
import random
from pathlib import Path


DEFAULT_SPECIAL_CHARS = "_-@#$()<>+"
COMMON_WORDS = [
    "data",
    "report",
    "image",
    "video",
    "cache",
    "config",
    "system",
    "record",
    "result",
    "backup",
    "archive",
    "project",
    "sample",
    "import",
    "export",
    "device",
    "client",
    "server",
    "access",
    "source",
    "target",
    "public",
    "private",
    "temp",
    "batch",
    "detail",
    "summary",
    "folder",
]


def get_resource_dir() -> Path:
    """获取配置、SQL、模板等资源文件所在目录。"""
    if getattr(sys, "frozen", False):
        external_dir = Path(sys.executable).resolve().parent
        if (external_dir / "sql").exists() and (external_dir / "config").exists():
            return external_dir
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent.parent


def get_output_dir() -> Path:
    """获取生成文件的输出目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "output"
    return Path(__file__).resolve().parent.parent / "output"


def create_random_relative_dir(
    base_dir: Path,
    levels: int,
    name_length: int = 8,
    special_chars: str = DEFAULT_SPECIAL_CHARS,
) -> Path:
    """在 base_dir 下创建随机层级目录，并返回相对路径。"""
    if levels <= 0:
        raise ValueError("目录层级必须大于 0。")
    relative_path = build_random_relative_dir_path(levels, name_length, special_chars)
    target_dir = base_dir / relative_path
    target_dir.mkdir(parents=True, exist_ok=True)
    return relative_path


def build_random_relative_dir_path(
    levels: int,
    name_length: int = 8,
    special_chars: str = DEFAULT_SPECIAL_CHARS,
) -> Path:
    """构造随机相对目录路径，不在文件系统中创建目录。"""
    if levels < 0:
        raise ValueError("目录层级不能小于 0。")
    if name_length <= 0:
        raise ValueError("目录名称长度必须大于 0。")
    if special_chars is None:
        special_chars = ""
    if levels == 0:
        return Path()

    return Path(*[_build_random_dir_name(name_length, special_chars) for _ in range(levels)])


def _build_random_dir_name(name_length: int, special_chars: str) -> str:
    """按单词、数字和特殊字符混合生成更像真实目录名的片段。"""
    parts = []

    while len("".join(parts)) < name_length:
        word = _randomize_word_style(random.choice(COMMON_WORDS))
        parts.append(word)

        if len("".join(parts)) < name_length and random.random() < 0.45:
            parts.append(str(random.randint(0, 9999)))

        if special_chars and len("".join(parts)) < name_length and random.random() < 0.3:
            parts.append(random.choice(special_chars))

    return "".join(parts)[:name_length]


def _randomize_word_style(word: str) -> str:
    """随机调整单词大小写风格，避免目录名过于单调。"""
    style = random.choice(("lower", "upper", "title", "camel"))
    if style == "upper":
        return word.upper()
    if style == "title":
        return word.capitalize()
    if style == "camel":
        pivot = random.randint(1, len(word) - 1)
        return word[:pivot].lower() + word[pivot:].capitalize()
    return word.lower()

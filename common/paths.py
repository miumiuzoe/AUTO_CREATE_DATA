import sys
from pathlib import Path


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

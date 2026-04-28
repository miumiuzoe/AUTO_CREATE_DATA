import random
from datetime import datetime, timedelta


def now_yyyymmdd() -> str:
    """返回当前日期，格式为 YYYYMMDD。"""
    return datetime.now().strftime("%Y%m%d")


def now_yyyymmddhhmmss() -> str:
    """返回当前日期时间，格式为 YYYYMMDDHHMMSS。"""
    return datetime.now().strftime("%Y%m%d%H%M%S")


def now_timestamp_ms() -> int:
    """返回当前时间戳值，保持兼容已有 fake.yml 规则。"""
    return int(datetime.now().timestamp())


def days_ago(days: int, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """返回当前时间向前推指定天数后的格式化时间。"""
    return (datetime.now() - timedelta(days=days)).strftime(fmt)


def days_later(days: int, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """返回当前时间向后推指定天数后的格式化时间。"""
    return (datetime.now() + timedelta(days=days)).strftime(fmt)


def random_datetime_between(
    start: str,
    end: str,
    fmt: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """返回开始时间和结束时间之间的随机格式化时间。"""
    start_dt = datetime.strptime(start, fmt)
    end_dt = datetime.strptime(end, fmt)
    if end_dt < start_dt:
        raise ValueError("结束时间不能早于开始时间。")

    total_seconds = int((end_dt - start_dt).total_seconds())
    offset = random.randint(0, total_seconds) if total_seconds > 0 else 0
    return (start_dt + timedelta(seconds=offset)).strftime(fmt)


def random_date_between(
    start: str,
    end: str,
    fmt: str = "%Y-%m-%d",
) -> str:
    """返回开始日期和结束日期之间的随机格式化日期。"""
    return random_datetime_between(start, end, fmt)

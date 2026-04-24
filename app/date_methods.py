import random
from datetime import datetime, timedelta


def now_yyyymmdd() -> str:
    """
    返回当前日期，格式为 YYYYMMDD。
    """
    return datetime.now().strftime("%Y%m%d")


def now_yyyymmddhhmmss() -> str:
    """
    返回当前日期时间，格式为 YYYYMMDDHHMMSS。
    """
    return datetime.now().strftime("%Y%m%d%H%M%S")


def now_timestamp_ms() -> int:
    """
    返回当前 13 位毫秒时间戳。
    """
    return int(datetime.now().timestamp())


def days_ago(days: int, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    返回当前时间往前推指定天数后的时间字符串。

    参数:
    days: 往前推的天数。
    fmt: 返回结果格式，默认 "%Y-%m-%d %H:%M:%S"。
    """
    return (datetime.now() - timedelta(days=days)).strftime(fmt)


def days_later(days: int, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    返回当前时间往后推指定天数后的时间字符串。

    参数:
    days: 往后推的天数。
    fmt: 返回结果格式，默认 "%Y-%m-%d %H:%M:%S"。
    """
    return (datetime.now() + timedelta(days=days)).strftime(fmt)


def random_datetime_between(
    start: str,
    end: str,
    fmt: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """
    在开始时间和结束时间之间随机生成一个时间点，并按指定格式返回。

    参数:
    start: 开始时间字符串，格式需与 fmt 一致。
    end: 结束时间字符串，格式需与 fmt 一致。
    fmt: 时间格式，默认 "%Y-%m-%d %H:%M:%S"。
    """
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
    """
    在开始日期和结束日期之间随机生成一个日期，并按指定格式返回。

    参数:
    start: 开始日期字符串，格式需与 fmt 一致。
    end: 结束日期字符串，格式需与 fmt 一致。
    fmt: 日期格式，默认 "%Y-%m-%d"。
    """
    return random_datetime_between(start, end, fmt)

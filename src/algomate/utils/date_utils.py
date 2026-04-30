"""
日期时间工具函数模块

提供日期时间的常用处理功能：
- 格式化和解析日期时间
- 计算日期间隔
- 获取相对时间描述
- 艾宾浩斯修炼日期计算

所有函数支持 timezone-aware 和 timezone-naive 两种 datetime 对象。
"""

from datetime import datetime, timedelta, date, timezone
from typing import Optional, Union


def now() -> datetime:
    """获取当前日期时间

    Returns:
        当前时刻的 datetime 对象
    """
    return datetime.now()


def today() -> date:
    """获取当前日期

    Returns:
        今天的 date 对象
    """
    return datetime.now().date()


def format_datetime(
    dt: datetime,
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """格式化日期时间为字符串

    Args:
        dt: datetime 对象
        format_str: 格式化模板，默认为 "YYYY-MM-DD HH:mm:ss"

    Returns:
        格式化后的日期时间字符串

    Example:
        >>> dt = datetime(2024, 1, 15, 10, 30, 0)
        >>> format_datetime(dt)
        '2024-01-15 10:30:00'
        >>> format_datetime(dt, "%Y年%m月%d日")
        '2024年01月15日'
    """
    return dt.strftime(format_str)


def format_date(d: date, format_str: str = "%Y-%m-%d") -> str:
    """格式化日期为字符串

    Args:
        d: date 对象
        format_str: 格式化模板，默认为 "YYYY-MM-DD"

    Returns:
        格式化后的日期字符串
    """
    return d.strftime(format_str)


def parse_datetime(
    date_str: str,
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> datetime:
    """解析字符串为 datetime 对象

    Args:
        date_str: 日期时间字符串
        format_str: 格式化模板

    Returns:
        datetime 对象

    Raises:
        ValueError: 当字符串格式不匹配时抛出

    Example:
        >>> parse_datetime("2024-01-15 10:30:00")
        datetime.datetime(2024, 1, 15, 10, 30)
    """
    return datetime.strptime(date_str, format_str)


def parse_date(date_str: str, format_str: str = "%Y-%m-%d") -> date:
    """解析字符串为 date 对象

    Args:
        date_str: 日期字符串
        format_str: 格式化模板

    Returns:
        date 对象
    """
    return datetime.strptime(date_str, format_str).date()


def parse_relative_time(date_str: str) -> datetime:
    """解析相对时间字符串

    支持的格式：
    - "1d", "2d" - 天数
    - "1h", "2h" - 小时数
    - "30m", "45m" - 分钟数
    - "1w", "2w" - 周数

    Args:
        date_str: 相对时间字符串

    Returns:
        计算后的 datetime 对象

    Example:
        >>> now = datetime.now()
        >>> parse_relative_time("1d")  # 一天后
    """
    date_str = date_str.strip().lower()

    units = {
        "w": ("weeks", 7 * 24 * 60),
        "d": ("days", 24 * 60),
        "h": ("hours", 60),
        "m": ("minutes", 1)
    }

    for unit, (name, minutes) in units.items():
        if date_str.endswith(unit):
            value = int(date_str[:-1])
            return datetime.now() + timedelta(**{name: value * minutes // minutes if minutes > 1 else value})

    raise ValueError(f"无法解析相对时间字符串: {date_str}")


def days_between(
    start: Union[datetime, date],
    end: Union[datetime, date]
) -> int:
    """计算两个日期之间的天数差

    Args:
        start: 开始日期
        end: 结束日期

    Returns:
        天数差（end - start），可为负数

    Example:
        >>> d1 = date(2024, 1, 1)
        >>> d2 = date(2024, 1, 10)
        >>> days_between(d1, d2)
        9
    """
    delta = end - start
    return delta.days


def add_days(dt: Union[datetime, date], days: int) -> Union[datetime, date]:
    """给日期增加指定天数

    Args:
        dt: 原始日期
        days: 要增加的天数（负数表示减）

    Returns:
        增加天数后的日期

    Example:
        >>> dt = date(2024, 1, 1)
        >>> add_days(dt, 7)
        datetime.date(2024, 1, 8)
    """
    return dt + timedelta(days=days)


def add_weeks(dt: Union[datetime, date], weeks: int) -> Union[datetime, date]:
    """给日期增加指定周数

    Args:
        dt: 原始日期
        weeks: 要增加的周数

    Returns:
        增加周数后的日期
    """
    return dt + timedelta(weeks=weeks)


def get_week_start(dt: Union[datetime, date]) -> date:
    """获取指定日期所在周的第一天（周一）

    Args:
        dt: 日期

    Returns:
        该周周一的日期
    """
    dt_date = dt.date() if isinstance(dt, datetime) else dt
    weekday = dt_date.weekday()
    return dt_date - timedelta(days=weekday)


def get_month_start(dt: Union[datetime, date]) -> date:
    """获取指定日期所在月的第一天

    Args:
        dt: 日期

    Returns:
        该月第一天的日期
    """
    dt_date = dt.date() if isinstance(dt, datetime) else dt
    return dt_date.replace(day=1)


def get_quarter_start(dt: Union[datetime, date]) -> date:
    """获取指定日期所在季度的第一天

    Args:
        dt: 日期

    Returns:
        该季度第一天的日期
    """
    dt_date = dt.date() if isinstance(dt, datetime) else dt
    quarter = (dt_date.month - 1) // 3
    month = quarter * 3 + 1
    return dt_date.replace(month=month, day=1)


def is_weekend(dt: Union[datetime, date]) -> bool:
    """判断是否为周末

    Args:
        dt: 日期

    Returns:
        周六或周日返回 True
    """
    dt_date = dt.date() if isinstance(dt, datetime) else dt
    return dt_date.weekday() in (5, 6)


def is_same_day(
    dt1: Union[datetime, date],
    dt2: Union[datetime, date]
) -> bool:
    """判断两个日期是否为同一天

    Args:
        dt1: 第一个日期
        dt2: 第二个日期

    Returns:
        同一天返回 True
    """
    d1 = dt1.date() if isinstance(dt1, datetime) else dt1
    d2 = dt2.date() if isinstance(dt2, datetime) else dt2
    return d1 == d2


def is_today(dt: Union[datetime, date]) -> bool:
    """判断是否为今天

    Args:
        dt: 日期

    Returns:
        今天返回 True
    """
    return is_same_day(dt, datetime.now())


def get_relative_description(dt: Union[datetime, date]) -> str:
    """获取相对时间描述

    Args:
        dt: 日期时间

    Returns:
        相对时间的中文描述

    Example:
        >>> get_relative_description(datetime.now() - timedelta(days=1))
        '昨天'
        >>> get_relative_description(datetime.now() + timedelta(hours=2))
        '2小时后'
    """
    dt_date = dt.date() if isinstance(dt, datetime) else dt
    now_date = datetime.now().date()

    delta_days = (dt_date - now_date).days

    if delta_days == 0:
        if isinstance(dt, datetime):
            delta_seconds = (dt - datetime.now()).total_seconds()
            if abs(delta_seconds) < 60:
                return "刚刚"
            hours = int(delta_seconds // 3600)
            if hours == 0:
                minutes = int(delta_seconds // 60)
                return f"{minutes}分钟后" if delta_seconds > 0 else f"{-minutes}分钟前"
            return f"{hours}小时后" if delta_seconds > 0 else f"{-hours}小时前"
        return "今天"
    elif delta_days == 1:
        return "明天"
    elif delta_days == -1:
        return "昨天"
    elif delta_days > 1 and delta_days <= 7:
        return f"{delta_days}天后"
    elif delta_days < -1 and delta_days >= -7:
        return f"{-delta_days}天前"
    else:
        if isinstance(dt, datetime):
            return format_datetime(dt, "%Y-%m-%d %H:%M")
        return format_date(dt)


def calculate_review_dates(
    start_date: datetime,
    intervals: list,
    include_initial: bool = True
) -> list:
    """计算艾宾浩斯修炼日期序列

    根据修炼间隔计算一系列修炼时间点，常用于修习类应用。

    标准艾宾浩斯间隔：1, 3, 7, 14, 30, 60 天

    Args:
        start_date: 首次修习/功力日期
        intervals: 修炼间隔天数列表
        include_initial: 是否包含起始日期作为第一个修炼点

    Returns:
        修炼日期列表（datetime 对象）

    Example:
        >>> start = datetime(2024, 1, 1)
        >>> dates = calculate_review_dates(start, [1, 3, 7, 14, 30])
        >>> len(dates)
        6
    """
    review_dates = []
    current_date = start_date

    if include_initial:
        review_dates.append(current_date)

    for interval in intervals:
        current_date = current_date + timedelta(days=interval)
        review_dates.append(current_date)

    return review_dates


def get_next_review_info(
    review_dates: list,
    current_date: Optional[datetime] = None
) -> dict:
    """获取下一次修炼的信息

    Args:
        review_dates: 修炼日期列表（已排序）
        current_date: 当前日期，默认为 datetime.now()

    Returns:
        包含 next_review（下次修炼日期）、remaining（剩余天数）、index（第几次修炼）的字典

    Example:
        >>> dates = calculate_review_dates(datetime.now(), [1, 3, 7])
        >>> info = get_next_review_info(dates)
        >>> info["remaining"]  # 距离下次修炼的天数
    """
    if current_date is None:
        current_date = datetime.now()

    for i, review_date in enumerate(review_dates):
        if review_date > current_date:
            return {
                "next_review": review_date,
                "remaining": (review_date - current_date).days,
                "index": i + 1,
                "is_overdue": False
            }

    return {
        "next_review": None,
        "remaining": 0,
        "index": len(review_dates),
        "is_overdue": True
    }


def ensure_timezone(dt: datetime, tz: Optional[timezone] = None) -> datetime:
    """确保 datetime 对象带有时区信息

    Args:
        dt: datetime 对象
        tz: 时区对象，默认为本地时区

    Returns:
        带时区信息的 datetime 对象
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz or datetime.now().astimezone().tzinfo)
    return dt


def to_utc(dt: datetime) -> datetime:
    """将 datetime 转换为 UTC 时区

    Args:
        dt: datetime 对象

    Returns:
        UTC 时区的 datetime 对象
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return dt.astimezone(timezone.utc)


class DateRange:
    """日期范围类

    用于处理日期范围的迭代和查询。

    Example:
        >>> date_range = DateRange(date(2024, 1, 1), date(2024, 1, 7))
        >>> for d in date_range:
        ...     print(d)
    """

    def __init__(self, start: date, end: date):
        """初始化日期范围

        Args:
            start: 起始日期（包含）
            end: 结束日期（包含）
        """
        self.start = start
        self.end = end

    def __iter__(self):
        """迭代器：按天迭代日期范围"""
        current = self.start
        while current <= self.end:
            yield current
            current += timedelta(days=1)

    def __len__(self) -> int:
        """返回日期范围内的天数"""
        return (self.end - self.start).days + 1

    def contains(self, dt: date) -> bool:
        """判断日期是否在范围内

        Args:
            dt: 日期

        Returns:
            在范围内返回 True
        """
        return self.start <= dt <= self.end

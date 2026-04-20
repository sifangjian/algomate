"""
Algomate 工具模块

提供通用的工具函数和类：
- Markdown 文档解析与渲染
- 日期时间处理工具
"""

from algomate.utils.markdown_parser import (
    MarkdownParser,
    CodeBlock,
    MarkdownSection,
    ParsedMarkdown,
    parse_markdown,
    markdown_to_html,
)

from algomate.utils.date_utils import (
    now,
    today,
    format_datetime,
    format_date,
    parse_datetime,
    parse_date,
    parse_relative_time,
    days_between,
    add_days,
    add_weeks,
    get_week_start,
    get_month_start,
    get_quarter_start,
    is_weekend,
    is_same_day,
    is_today,
    get_relative_description,
    calculate_review_dates,
    get_next_review_info,
    ensure_timezone,
    to_utc,
    DateRange,
)

__all__ = [
    # markdown_parser
    "MarkdownParser",
    "CodeBlock",
    "MarkdownSection",
    "ParsedMarkdown",
    "parse_markdown",
    "markdown_to_html",
    # date_utils
    "now",
    "today",
    "format_datetime",
    "format_date",
    "parse_datetime",
    "parse_date",
    "parse_relative_time",
    "days_between",
    "add_days",
    "add_weeks",
    "get_week_start",
    "get_month_start",
    "get_quarter_start",
    "is_weekend",
    "is_same_day",
    "is_today",
    "get_relative_description",
    "calculate_review_dates",
    "get_next_review_info",
    "ensure_timezone",
    "to_utc",
    "DateRange",
]

"""
遗忘曲线算法模块

基于艾宾浩斯遗忘曲线理论，实现科学的复习间隔计算：
- 根据掌握程度计算下次复习时间
- 生成笔记的完整复习计划
- 根据答题情况更新掌握程度

复习间隔遵循艾宾浩斯遗忘曲线：1天、3天、7天、14天、30天、60天
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from ...config.settings import AppConfig


class ForgottenCurve:
    """遗忘曲线算法类

    基于艾宾浩斯遗忘曲线理论，计算最优复习时机。

    核心原理：
    - 记忆越深刻，复习间隔越长
    - 掌握程度越高，增长系数越大
    - 答错时缩短间隔，答对时延长间隔

    Attributes:
        intervals: 复习间隔天数列表
    """

    def __init__(self, intervals: List[int] = None):
        """初始化遗忘曲线计算器

        Args:
            intervals: 自定义复习间隔列表，默认为配置中的间隔
        """
        config = AppConfig.load()
        self.intervals = intervals or config.REVIEW_INTERVALS

    def calculate_next_review(
        self, mastery_level: int, review_count: int, last_review_date: datetime
    ) -> datetime:
        """计算下次复习时间

        根据当前掌握程度和复习次数，计算最佳复习时间点。

        Args:
            mastery_level: 掌握程度（0-100）
            review_count: 已复习次数
            last_review_date: 上次复习时间

        Returns:
            下次复习的日期时间
        """
        if mastery_level >= 90:
            interval = self.intervals[-1] * 2
        elif mastery_level >= 70:
            idx = min(review_count, len(self.intervals) - 1)
            interval = self.intervals[idx] * 1.5
        elif mastery_level >= 50:
            idx = min(review_count, len(self.intervals) - 1)
            interval = self.intervals[idx]
        else:
            interval = self.intervals[0]

        return last_review_date + timedelta(days=int(interval))

    def get_review_schedule(self, note_id: int, created_at: datetime) -> List[Dict[str, Any]]:
        """生成复习计划

        为新笔记生成完整的复习时间表。

        Args:
            note_id: 笔记ID
            created_at: 笔记创建时间

        Returns:
            复习计划列表，每项包含日期、间隔、是否关键复习点
        """
        schedule = []
        current_date = created_at

        for i, interval in enumerate(self.intervals):
            review_date = current_date + timedelta(days=interval)
            schedule.append({
                "note_id": note_id,
                "review_date": review_date,
                "interval": interval,
                "is_key_review": interval in [7, 14, 30],
            })
            current_date = review_date

        return schedule

    def update_mastery_level(
        self, current_level: int, is_correct: bool, difficulty: str
    ) -> int:
        """更新掌握程度

        根据答题结果调整掌握程度。

        Args:
            current_level: 当前掌握程度
            is_correct: 答题是否正确
            difficulty: 题目难度（简单/中等/困难）

        Returns:
            新的掌握程度（0-100）
        """
        difficulty_factor = {
            "简单": 5,
            "中等": 10,
            "困难": 15,
        }.get(difficulty, 10)

        if is_correct:
            increment = difficulty_factor * (1 + current_level / 100)
            new_level = min(100, current_level + increment)
        else:
            decrement = difficulty_factor * 0.5
            new_level = max(0, current_level - decrement)

        return int(new_level)

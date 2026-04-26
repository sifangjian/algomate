"""
遗忘曲线引擎模块

基于艾宾浩斯遗忘曲线理论，实现科学的复习时间节点计算：
- 复习节点：创建 → 1天 → 3天 → 7天 → 14天 → 30天 → 60天
- 复习成功后推进到下一个节点
- 复习失败后退回到前一个节点

核心算法：
    复习节点：[1, 3, 7, 14, 30, 60] 天
    复习等级：1-7级（0级为初始状态，1-6级对应6个复习节点）
"""

from datetime import datetime, timedelta, date
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from algomate.config.settings import AppConfig


class ReviewAction(str, Enum):
    """复习动作枚举"""
    SUCCESS = "success"
    FAIL = "fail"


@dataclass
class ReviewResult:
    """复习结果数据结构
    
    Attributes:
        next_review_date: 下次复习日期
        review_level: 复习等级（0-6）
        is_due: 是否应该复习
    """
    next_review_date: date
    review_level: int
    is_due: bool


class ForgottenCurveEngine:
    """遗忘曲线引擎
    
    基于艾宾浩斯遗忘曲线理论，计算最优复习时机。
    
    核心原理：
        - 记忆越深刻，复习间隔越长
        - 复习成功推进到下一个节点
        - 复习失败退回到前一个节点
    
    Attributes:
        intervals: 复习间隔天数列表 [1, 3, 7, 14, 30, 60]
        max_level: 最大复习等级（6级）
    """
    
    DEFAULT_INTERVALS = [1, 3, 7, 14, 30, 60]
    
    def __init__(self, intervals: Optional[List[int]] = None):
        """初始化遗忘曲线引擎
        
        Args:
            intervals: 自定义复习间隔列表，默认为 [1, 3, 7, 14, 30, 60]
        """
        config = AppConfig.load()
        self.intervals = intervals or config.REVIEW_INTERVALS or self.DEFAULT_INTERVALS
        self.max_level = len(self.intervals)
    
    def get_review_interval(self, review_level: int) -> int:
        """获取指定复习等级的间隔天数
        
        Args:
            review_level: 复习等级（0-6）
                - 0级：初始状态，间隔为0天
                - 1-6级：对应复习节点 [1, 3, 7, 14, 30, 60]
        
        Returns:
            间隔天数
        
        Raises:
            ValueError: 当 review_level 超出范围时
        
        Example:
            >>> engine = ForgottenCurveEngine()
            >>> engine.get_review_interval(0)
            0
            >>> engine.get_review_interval(1)
            1
            >>> engine.get_review_interval(3)
            7
        """
        if review_level < 0 or review_level > self.max_level:
            raise ValueError(f"复习等级必须在 0-{self.max_level} 之间，当前为 {review_level}")
        
        if review_level == 0:
            return 0
        
        return self.intervals[review_level - 1]
    
    def calculate_next_review(
        self, 
        last_reviewed: datetime, 
        review_level: int,
        action: ReviewAction = ReviewAction.SUCCESS
    ) -> Tuple[datetime, int]:
        """计算下次复习时间和新的复习等级
        
        Args:
            last_reviewed: 上次复习时间
            review_level: 当前复习等级（0-6）
            action: 复习动作（成功/失败）
        
        Returns:
            (下次复习时间, 新的复习等级)
        
        Example:
            >>> engine = ForgottenCurveEngine()
            >>> last = datetime(2024, 1, 1, 10, 0)
            >>> next_review, new_level = engine.calculate_next_review(last, 1, ReviewAction.SUCCESS)
            >>> next_review.date()
            datetime.date(2024, 1, 4)  # 1级成功后推进到2级，间隔3天
            >>> new_level
            2
        """
        if action == ReviewAction.SUCCESS:
            new_level = min(review_level + 1, self.max_level)
        else:
            new_level = max(review_level - 1, 0)
        
        interval_days = self.get_review_interval(new_level)
        next_review = last_reviewed + timedelta(days=interval_days)
        
        return next_review, new_level
    
    def should_review(
        self, 
        created_at: datetime, 
        last_reviewed: Optional[datetime],
        review_level: int
    ) -> bool:
        """判断卡牌是否需要复习
        
        Args:
            created_at: 卡牌创建时间
            last_reviewed: 上次复习时间（None表示从未复习）
            review_level: 当前复习等级（0-6）
        
        Returns:
            是否应该复习
        
        Example:
            >>> engine = ForgottenCurveEngine()
            >>> created = datetime(2024, 1, 1, 10, 0)
            >>> # 从未复习，创建时间超过1天
            >>> engine.should_review(created, None, 0)
            True
            >>> # 刚复习过
            >>> last = datetime.now() - timedelta(hours=12)
            >>> engine.should_review(created, last, 1)
            False
        """
        now = datetime.now()
        
        if last_reviewed is None:
            interval_days = self.get_review_interval(review_level + 1) if review_level < self.max_level else self.intervals[-1]
            next_review = created_at + timedelta(days=interval_days)
        else:
            interval_days = self.get_review_interval(review_level)
            next_review = last_reviewed + timedelta(days=interval_days)
        
        return now >= next_review
    
    def get_review_status(
        self,
        created_at: datetime,
        last_reviewed: Optional[datetime],
        review_level: int
    ) -> ReviewResult:
        """获取复习状态详情
        
        Args:
            created_at: 卡牌创建时间
            last_reviewed: 上次复习时间
            review_level: 当前复习等级
        
        Returns:
            ReviewResult 包含下次复习日期、复习等级、是否应该复习
        """
        now = datetime.now()
        
        if last_reviewed is None:
            if review_level == 0:
                interval_days = self.get_review_interval(1)
                next_review_date = (created_at + timedelta(days=interval_days)).date()
            else:
                interval_days = self.get_review_interval(review_level)
                next_review_date = (created_at + timedelta(days=interval_days)).date()
        else:
            interval_days = self.get_review_interval(review_level)
            next_review_date = (last_reviewed + timedelta(days=interval_days)).date()
        
        is_due = now.date() >= next_review_date
        
        return ReviewResult(
            next_review_date=next_review_date,
            review_level=review_level,
            is_due=is_due
        )
    
    def get_daily_review_tasks(self, cards: List) -> List:
        """获取今日需要复习的卡牌列表
        
        Args:
            cards: 卡牌列表（需要包含 created_at, last_reviewed, review_level 属性）
        
        Returns:
            需要复习的卡牌列表（按优先级排序：濒危卡牌优先）
        
        Note:
            卡牌对象需要有以下属性：
            - created_at: datetime
            - last_reviewed: Optional[datetime]
            - review_level: int
            - durability: int (用于排序)
            - is_sealed: bool (封印卡牌不参与复习)
        """
        due_cards = []
        
        for card in cards:
            if hasattr(card, 'is_sealed') and card.is_sealed:
                continue
            
            if self.should_review(
                card.created_at,
                card.last_reviewed,
                getattr(card, 'review_level', 0)
            ):
                due_cards.append(card)
        
        due_cards.sort(key=lambda c: getattr(c, 'durability', 100))
        
        return due_cards
    
    def calculate_review_level_from_history(
        self, 
        created_at: datetime,
        last_reviewed: Optional[datetime],
        success_count: int = 0
    ) -> int:
        """根据历史复习记录计算复习等级
        
        Args:
            created_at: 卡牌创建时间
            last_reviewed: 上次复习时间
            success_count: 连续成功次数
        
        Returns:
            推断的复习等级
        
        Note:
            这是一个辅助函数，用于在没有明确记录复习等级时推断等级
        """
        if last_reviewed is None:
            return 0
        
        days_since_creation = (datetime.now() - created_at).days
        
        if days_since_creation < 1:
            return 0
        elif days_since_creation < 3:
            return 1
        elif days_since_creation < 7:
            return 2
        elif days_since_creation < 14:
            return 3
        elif days_since_creation < 30:
            return 4
        elif days_since_creation < 60:
            return 5
        else:
            return min(success_count, self.max_level)


def calculate_next_review(
    last_reviewed: datetime, 
    review_level: int,
    action: ReviewAction = ReviewAction.SUCCESS
) -> Tuple[datetime, int]:
    """计算下次复习时间（便捷函数）
    
    Args:
        last_reviewed: 上次复习时间
        review_level: 当前复习等级
        action: 复习动作
    
    Returns:
        (下次复习时间, 新的复习等级)
    """
    engine = ForgottenCurveEngine()
    return engine.calculate_next_review(last_reviewed, review_level, action)


def should_review(
    created_at: datetime,
    last_reviewed: Optional[datetime],
    review_level: int
) -> bool:
    """判断卡牌是否需要复习（便捷函数）
    
    Args:
        created_at: 卡牌创建时间
        last_reviewed: 上次复习时间
        review_level: 当前复习等级
    
    Returns:
        是否应该复习
    """
    engine = ForgottenCurveEngine()
    return engine.should_review(created_at, last_reviewed, review_level)


def get_review_interval(review_level: int) -> int:
    """获取指定复习等级的间隔天数（便捷函数）
    
    Args:
        review_level: 复习等级
    
    Returns:
        间隔天数
    """
    engine = ForgottenCurveEngine()
    return engine.get_review_interval(review_level)


def get_daily_review_tasks(cards: List) -> List:
    """获取今日需要复习的卡牌列表（便捷函数）
    
    Args:
        cards: 卡牌列表
    
    Returns:
        需要复习的卡牌列表
    """
    engine = ForgottenCurveEngine()
    return engine.get_daily_review_tasks(cards)

"""
遗忘曲线引擎模块

基于艾宾浩斯遗忘曲线理论，实现科学的修炼时间节点计算：
- 修炼节点：创建 → 1天 → 3天 → 7天 → 14天 → 30天 → 60天
- 修炼成功后推进到下一个节点
- 修炼失败后退回到前一个节点

核心算法：
    修炼节点：[1, 3, 7, 14, 30, 60] 天
    修炼等级：1-7级（0级为初始状态，1-6级对应6个修炼节点）
"""

from datetime import datetime, timedelta, date
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from algomate.config.settings import AppConfig


class ReviewAction(str, Enum):
    """修炼动作枚举"""
    SUCCESS = "success"
    FAIL = "fail"


@dataclass
class ReviewResult:
    """修炼结果数据结构
    
    Attributes:
        next_review_date: 下次修炼日期
        review_level: 修炼等级（0-6）
        is_due: 是否应该修炼
    """
    next_review_date: date
    review_level: int
    is_due: bool


class ForgottenCurveEngine:
    """遗忘曲线引擎
    
    基于艾宾浩斯遗忘曲线理论，计算最优修炼时机。
    
    核心原理：
        - 记忆越深刻，修炼间隔越长
        - 修炼成功推进到下一个节点
        - 修炼失败退回到前一个节点
    
    Attributes:
        intervals: 修炼间隔天数列表 [1, 3, 7, 14, 30, 60]
        max_level: 最大修炼等级（6级）
    """
    
    DEFAULT_INTERVALS = [1, 3, 7, 14, 30, 60]
    
    def __init__(self, intervals: Optional[List[int]] = None):
        """初始化遗忘曲线引擎
        
        Args:
            intervals: 自定义修炼间隔列表，默认为 [1, 3, 7, 14, 30, 60]
        """
        config = AppConfig.load()
        self.intervals = intervals or config.REVIEW_INTERVALS or self.DEFAULT_INTERVALS
        self.max_level = len(self.intervals)
    
    def get_review_interval(self, review_level: int) -> int:
        """获取指定修炼等级的间隔天数
        
        Args:
            review_level: 修炼等级（0-6）
                - 0级：初始状态，间隔为0天
                - 1-6级：对应修炼节点 [1, 3, 7, 14, 30, 60]
        
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
            raise ValueError(f"修炼等级必须在 0-{self.max_level} 之间，当前为 {review_level}")
        
        if review_level == 0:
            return 0
        
        return self.intervals[review_level - 1]
    
    def calculate_next_review(
        self, 
        last_reviewed: datetime, 
        review_level: int,
        action: ReviewAction = ReviewAction.SUCCESS
    ) -> Tuple[datetime, int]:
        """计算下次修炼时间和新的修炼等级
        
        Args:
            last_reviewed: 上次修炼时间
            review_level: 当前修炼等级（0-6）
            action: 修炼动作（成功/失败）
        
        Returns:
            (下次修炼时间, 新的修炼等级)
        
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
        """判断卡牌是否需要修炼
        
        Args:
            created_at: 卡牌创建时间
            last_reviewed: 上次修炼时间（None表示从未修炼）
            review_level: 当前修炼等级（0-6）
        
        Returns:
            是否应该修炼
        
        Example:
            >>> engine = ForgottenCurveEngine()
            >>> created = datetime(2024, 1, 1, 10, 0)
            >>> # 从未修炼，创建时间超过1天
            >>> engine.should_review(created, None, 0)
            True
            >>> # 刚修炼过
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
        """获取修炼状态详情
        
        Args:
            created_at: 卡牌创建时间
            last_reviewed: 上次修炼时间
            review_level: 当前修炼等级
        
        Returns:
            ReviewResult 包含下次修炼日期、修炼等级、是否应该修炼
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
        """获取今日需要修炼的卡牌列表
        
        Args:
            cards: 卡牌列表（Card 对象，包含 created_at, last_reviewed, review_level, durability, next_review_date 属性）
        
        Returns:
            需要修炼的卡牌列表（按优先级排序：耐久度低优先，到期日早优先）
        
        Note:
            卡牌对象需要有以下属性：
            - created_at: datetime
            - last_reviewed: Optional[datetime]
            - review_level: int
            - durability: int (用于排序)
            - next_review_date: Optional[datetime] (用于排序)
            - is_sealed: bool (封印卡牌不参与修炼)
        """
        due_cards = []
        
        for card in cards:
            if hasattr(card, 'is_sealed') and card.is_sealed:
                continue
            
            if self.should_review(
                card.created_at,
                card.last_reviewed,
                card.review_level
            ):
                due_cards.append(card)
        
        due_cards.sort(key=lambda c: (
            c.durability,
            c.next_review_date if c.next_review_date else datetime.max
        ))
        
        return due_cards
    
    def get_review_status_for_card(self, card) -> ReviewResult:
        """获取卡牌的修炼状态详情
        
        基于 Card 对象的 created_at、last_reviewed、review_level 字段，
        计算下次修炼日期和是否到期。
        
        Args:
            card: Card 对象，需包含 created_at, last_reviewed, review_level 属性
        
        Returns:
            ReviewResult 包含 next_review_date、review_level、is_due
        """
        return self.get_review_status(
            created_at=card.created_at,
            last_reviewed=card.last_reviewed,
            review_level=card.review_level
        )
    
    def complete_review_for_card(
        self, 
        card, 
        action: ReviewAction
    ) -> Tuple[int, date]:
        """完成一次卡牌修炼，计算新的修炼等级和下次修炼日期
        
        根据修炼动作（成功/失败）更新修炼等级，同时调整耐久度：
        - 修炼成功：review_level +1（不超过 max_level），durability +20（不超过 100）
        - 修炼失败：review_level -1（不低于 0），durability -5（不低于 0）
        
        Args:
            card: Card 对象，需包含 last_reviewed, review_level, durability 属性
            action: 修炼动作（SUCCESS / FAIL）
        
        Returns:
            (new_review_level, next_review_date) 元组
        """
        now = datetime.now()
        last_reviewed = card.last_reviewed or card.created_at or now
        
        next_review_dt, new_level = self.calculate_next_review(
            last_reviewed=last_reviewed,
            review_level=card.review_level,
            action=action
        )
        
        if action == ReviewAction.SUCCESS:
            card.durability = min(card.durability + 20, card.max_durability if hasattr(card, 'max_durability') else 100)
        else:
            card.durability = max(card.durability - 5, 0)
        
        card.review_level = new_level
        card.next_review_date = next_review_dt
        card.last_reviewed = now
        card.review_count = getattr(card, 'review_count', 0) + 1
        
        return new_level, next_review_dt.date()
    
    def calculate_review_level_from_history(
        self, 
        created_at: datetime,
        last_reviewed: Optional[datetime],
        success_count: int = 0
    ) -> int:
        """根据历史修炼记录计算修炼等级
        
        Args:
            created_at: 卡牌创建时间
            last_reviewed: 上次修炼时间
            success_count: 连续成功次数
        
        Returns:
            推断的修炼等级
        
        Note:
            这是一个辅助函数，用于在没有明确记录修炼等级时推断等级
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
    """计算下次修炼时间（便捷函数）
    
    Args:
        last_reviewed: 上次修炼时间
        review_level: 当前修炼等级
        action: 修炼动作
    
    Returns:
        (下次修炼时间, 新的修炼等级)
    """
    engine = ForgottenCurveEngine()
    return engine.calculate_next_review(last_reviewed, review_level, action)


def should_review(
    created_at: datetime,
    last_reviewed: Optional[datetime],
    review_level: int
) -> bool:
    """判断卡牌是否需要修炼（便捷函数）
    
    Args:
        created_at: 卡牌创建时间
        last_reviewed: 上次修炼时间
        review_level: 当前修炼等级
    
    Returns:
        是否应该修炼
    """
    engine = ForgottenCurveEngine()
    return engine.should_review(created_at, last_reviewed, review_level)


def get_review_interval(review_level: int) -> int:
    """获取指定修炼等级的间隔天数（便捷函数）
    
    Args:
        review_level: 修炼等级
    
    Returns:
        间隔天数
    """
    engine = ForgottenCurveEngine()
    return engine.get_review_interval(review_level)


def get_daily_review_tasks(cards: List) -> List:
    """获取今日需要修炼的卡牌列表（便捷函数）
    
    Args:
        cards: 卡牌列表
    
    Returns:
        需要修炼的卡牌列表
    """
    engine = ForgottenCurveEngine()
    return engine.get_daily_review_tasks(cards)

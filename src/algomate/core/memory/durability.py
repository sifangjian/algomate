"""
耐久度管理模块

管理卡牌耐久度的增减，包括：
- 修炼成功/失败的耐久度变化
- 每日衰减机制
- 濒危和消散状态判断
"""

from datetime import datetime, timedelta, date
from enum import Enum
from typing import Optional, Tuple
from dataclasses import dataclass

GRACE_PERIOD_DAYS = 3


class DurabilityAction(str, Enum):
    """耐久度变化动作枚举"""
    REVIEW_SUCCESS = "review_success"
    REVIEW_FAIL = "review_fail"
    DAILY_DECAY = "daily_decay"


@dataclass
class DurabilityConfig:
    """耐久度配置数据结构

    Attributes:
        success_base: 修炼成功基础增量
        fail_base: 修炼失败基础减量
        daily_decay_base: 每日衰减基础减量
        critical_threshold: 濒危阈值
        sealed_threshold: 封印阈值
        max_durability: 最大耐久度
        min_durability: 最小耐久度
    """
    success_base: int = 20
    fail_base: int = 5
    daily_decay_base: int = 2
    critical_threshold: int = 30
    sealed_threshold: int = 0
    max_durability: int = 100
    min_durability: int = 0


class DurabilityManager:
    """耐久度管理器

    管理卡牌耐久度的增减，判断濒危和消散状态。

    Attributes:
        config: 耐久度配置
    """

    def __init__(self, config: Optional[DurabilityConfig] = None):
        self.config = config or DurabilityConfig()

    @staticmethod
    def is_in_grace_period(created_at: Optional[datetime]) -> bool:
        if created_at is None:
            return False
        return created_at.date() + timedelta(days=GRACE_PERIOD_DAYS) > date.today()

    def update_durability(
        self,
        current_durability: int,
        action: DurabilityAction,
        difficulty_multiplier: float = 1.0
    ) -> Tuple[int, bool, bool]:
        """更新耐久度

        Args:
            current_durability: 当前耐久度
            action: 耐久度变化动作
            difficulty_multiplier: 难度系数

        Returns:
            (新耐久度, 是否濒危, 是否需要重修)
        """
        if action == DurabilityAction.REVIEW_SUCCESS:
            base_change = self.config.success_base
        elif action == DurabilityAction.REVIEW_FAIL:
            base_change = -self.config.fail_base
        elif action == DurabilityAction.DAILY_DECAY:
            base_change = -self.config.daily_decay_base
        else:
            base_change = 0

        change = int(base_change * difficulty_multiplier)
        new_durability = current_durability + change

        new_durability = max(
            self.config.min_durability,
            min(self.config.max_durability, new_durability)
        )

        is_critical = new_durability < self.config.critical_threshold
        needs_retake = new_durability == self.config.sealed_threshold

        return new_durability, is_critical, needs_retake

    def is_critical(self, durability: int) -> bool:
        return durability < self.config.critical_threshold

    def needs_retake(self, durability: int) -> bool:
        return durability == self.config.sealed_threshold

    def unseal_durability(self) -> int:
        return 80


def apply_daily_decay(card, difficulty_multiplier: float = 1.0) -> dict:
    """对单张卡牌应用每日衰减"""
    manager = DurabilityManager()

    if getattr(card, 'pending_retake', False):
        return {
            "card": card,
            "old_durability": getattr(card, 'durability', 80),
            "new_durability": getattr(card, 'durability', 80),
            "status": "pending_retake",
            "decayed": False,
        }

    if hasattr(card, 'created_at') and manager.is_in_grace_period(card.created_at):
        return {
            "card": card,
            "old_durability": getattr(card, 'durability', 80),
            "new_durability": getattr(card, 'durability', 80),
            "status": "normal",
            "decayed": False,
        }

    current_durability = getattr(card, 'durability', 80)
    new_durability, is_critical, needs_retake = manager.update_durability(
        current_durability,
        DurabilityAction.DAILY_DECAY,
        difficulty_multiplier
    )

    return {
        "card": card,
        "old_durability": current_durability,
        "new_durability": new_durability,
        "status": "pending_retake" if needs_retake else ("endangered" if is_critical else "normal"),
        "decayed": True,
    }
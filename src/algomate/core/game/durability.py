"""
耐久度管理系统模块

管理卡牌耐久度的增减，包括：
- 修炼成功/失败的耐久度变化
- 每日衰减机制
- 濒危和消散状态判断
- 难度系数应用

耐久度规则：
    - 范围：0-100
    - 修炼成功：+20 × 难度系数
    - 修炼失败：-5 × 难度系数
    - 每日衰减：-2 × 难度系数
    - 濒危阈值：<30
    - 消散阈值：=0（卡牌封印）
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
    BOSS_DEFEAT = "boss_defeat"
    BOSS_FAIL = "boss_fail"


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
    
    管理卡牌耐久度的增减，应用难度系数，判断濒危和消散状态。
    
    Attributes:
        config: 耐久度配置
        difficulty_multipliers: 难度系数映射
    """
    
    DEFAULT_DIFFICULTY_MULTIPLIERS = {
        "easy": 0.5,
        "normal": 1.0,
        "hard": 1.5,
    }
    
    def __init__(
        self, 
        config: Optional[DurabilityConfig] = None,
        difficulty_multipliers: Optional[dict] = None
    ):
        """初始化耐久度管理器
        
        Args:
            config: 耐久度配置，默认使用默认配置
            difficulty_multipliers: 自定义难度系数映射
        """
        self.config = config or DurabilityConfig()
        self.difficulty_multipliers = difficulty_multipliers or self.DEFAULT_DIFFICULTY_MULTIPLIERS
    
    @staticmethod
    def is_in_grace_period(created_at: Optional[datetime]) -> bool:
        if created_at is None:
            return False
        return created_at.date() + timedelta(days=GRACE_PERIOD_DAYS) > date.today()
    
    def get_difficulty_multiplier(self, difficulty: str) -> float:
        """获取难度系数
        
        Args:
            difficulty: 难度等级（easy/normal/hard）
        
        Returns:
            难度系数
        
        Example:
            >>> manager = DurabilityManager()
            >>> manager.get_difficulty_multiplier("easy")
            0.5
            >>> manager.get_difficulty_multiplier("normal")
            1.0
            >>> manager.get_difficulty_multiplier("hard")
            1.5
        """
        return self.difficulty_multipliers.get(difficulty, 1.0)
    
    def calculate_durability_change(
        self, 
        action: DurabilityAction, 
        difficulty: str = "normal"
    ) -> int:
        """计算耐久度变化值
        
        Args:
            action: 耐久度变化动作
            difficulty: 难度等级
        
        Returns:
            耐久度变化值（正数为增加，负数为减少）
        
        Example:
            >>> manager = DurabilityManager()
            >>> manager.calculate_durability_change(DurabilityAction.REVIEW_SUCCESS, "normal")
            20
            >>> manager.calculate_durability_change(DurabilityAction.REVIEW_FAIL, "hard")
            -7  # -5 * 1.5 = -7.5，向下取整为 -7
        """
        multiplier = self.get_difficulty_multiplier(difficulty)
        
        if action in [DurabilityAction.REVIEW_SUCCESS, DurabilityAction.BOSS_DEFEAT]:
            base_change = self.config.success_base
            return int(base_change * multiplier)
        elif action in [DurabilityAction.REVIEW_FAIL, DurabilityAction.BOSS_FAIL]:
            base_change = self.config.fail_base
            return -int(base_change * multiplier)
        elif action == DurabilityAction.DAILY_DECAY:
            base_change = self.config.daily_decay_base
            return -int(base_change * multiplier)
        else:
            return 0
    
    def update_durability(
        self, 
        current_durability: int, 
        action: DurabilityAction,
        difficulty: str = "normal"
    ) -> Tuple[int, bool, bool]:
        """更新耐久度
        
        Args:
            current_durability: 当前耐久度
            action: 耐久度变化动作
            difficulty: 难度等级
        
        Returns:
            (新耐久度, 是否濒危, 是否封印)
        
        Example:
            >>> manager = DurabilityManager()
            >>> new_dur, is_critical, is_sealed = manager.update_durability(
            ...     80, DurabilityAction.REVIEW_SUCCESS, "normal"
            ... )
            >>> new_dur
            100
            >>> is_critical
            False
            >>> is_sealed
            False
        """
        change = self.calculate_durability_change(action, difficulty)
        new_durability = current_durability + change
        
        new_durability = max(
            self.config.min_durability, 
            min(self.config.max_durability, new_durability)
        )
        
        is_critical = new_durability < self.config.critical_threshold
        is_sealed = new_durability == self.config.sealed_threshold
        
        return new_durability, is_critical, is_sealed
    
    def is_critical(self, durability: int) -> bool:
        """判断是否濒危
        
        Args:
            durability: 耐久度
        
        Returns:
            是否濒危
        """
        return durability < self.config.critical_threshold
    
    def is_sealed(self, durability: int) -> bool:
        """判断是否封印
        
        Args:
            durability: 耐久度
        
        Returns:
            是否封印
        """
        return durability == self.config.sealed_threshold
    
    def unseal_durability(self) -> int:
        """解封卡牌时的耐久度恢复值
        
        Returns:
            解封后的耐久度（默认恢复至30）
        """
        return self.config.critical_threshold
    
    def get_durability_status(self, durability: int) -> dict:
        """获取耐久度状态详情
        
        Args:
            durability: 耐久度
        
        Returns:
            状态字典，包含耐久度、是否濒危、是否封印、状态描述
        """
        is_critical = self.is_critical(durability)
        is_sealed = self.is_sealed(durability)
        
        if is_sealed:
            status = "封印"
            description = "卡牌已消散，需要通过修炼解封"
        elif is_critical:
            status = "濒危"
            description = "卡牌耐久度过低，建议尽快修炼"
        else:
            status = "正常"
            description = "卡牌状态良好"
        
        return {
            "durability": durability,
            "is_critical": is_critical,
            "is_sealed": is_sealed,
            "status": status,
            "description": description,
        }
    
    def apply_daily_decay_to_cards(
        self, 
        cards: list, 
        difficulty: str = "normal"
    ) -> list:
        """批量应用每日衰减
        
        Args:
            cards: 卡牌列表（需要有 durability 和 is_sealed 属性）
            difficulty: 难度等级
        
        Returns:
            需要更新的卡牌列表（包含新的耐久度值）
        
        Note:
            封印的卡牌不参与每日衰减
        """
        updated_cards = []
        
        for card in cards:
            if hasattr(card, 'is_sealed') and card.is_sealed:
                continue
            
            if hasattr(card, 'created_at') and self.is_in_grace_period(card.created_at):
                continue
            
            current_durability = getattr(card, 'durability', 100)
            new_durability, is_critical, is_sealed = self.update_durability(
                current_durability,
                DurabilityAction.DAILY_DECAY,
                difficulty
            )
            
            updated_cards.append({
                "card": card,
                "old_durability": current_durability,
                "new_durability": new_durability,
                "is_critical": is_critical,
                "is_sealed": is_sealed,
            })
        
        return updated_cards


def update_durability(
    current_durability: int,
    action: DurabilityAction,
    difficulty: str = "normal"
) -> Tuple[int, bool, bool]:
    """更新耐久度（便捷函数）
    
    Args:
        current_durability: 当前耐久度
        action: 耐久度变化动作
        difficulty: 难度等级
    
    Returns:
        (新耐久度, 是否濒危, 是否封印)
    """
    manager = DurabilityManager()
    return manager.update_durability(current_durability, action, difficulty)


def get_critical_cards(cards: list) -> list:
    """获取所有濒危卡牌（便捷函数）
    
    Args:
        cards: 卡牌列表
    
    Returns:
        濒危卡牌列表
    """
    manager = DurabilityManager()
    return [
        card for card in cards
        if not getattr(card, 'is_sealed', False)
        and manager.is_critical(getattr(card, 'durability', 100))
    ]


def unseal_card(durability: int) -> int:
    """解封卡牌（便捷函数）
    
    Args:
        durability: 当前耐久度
    
    Returns:
        解封后的耐久度
    """
    manager = DurabilityManager()
    return manager.unseal_durability()


def compute_card_status(durability: int, pending_retake: bool) -> str:
    if pending_retake or durability == 0:
        return "pending_retake"
    if durability < 30:
        return "endangered"
    return "normal"


def apply_daily_decay(card, difficulty: str = "normal") -> dict:
    manager = DurabilityManager()
    
    if getattr(card, 'pending_retake', False) or getattr(card, 'is_sealed', False):
        return {
            "card": card,
            "old_durability": getattr(card, 'durability', 80),
            "new_durability": getattr(card, 'durability', 80),
            "status": compute_card_status(
                getattr(card, 'durability', 80),
                getattr(card, 'pending_retake', False)
            ),
            "decayed": False,
        }
    
    if hasattr(card, 'created_at') and manager.is_in_grace_period(card.created_at):
        return {
            "card": card,
            "old_durability": getattr(card, 'durability', 80),
            "new_durability": getattr(card, 'durability', 80),
            "status": compute_card_status(
                getattr(card, 'durability', 80),
                getattr(card, 'pending_retake', False)
            ),
            "decayed": False,
        }
    
    current_durability = getattr(card, 'durability', 80)
    new_durability, is_critical, is_sealed = manager.update_durability(
        current_durability,
        DurabilityAction.DAILY_DECAY,
        difficulty
    )
    
    return {
        "card": card,
        "old_durability": current_durability,
        "new_durability": new_durability,
        "status": compute_card_status(new_durability, False),
        "decayed": True,
    }

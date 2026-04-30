"""
游戏难度参数系统模块

提供不同难度等级的游戏参数，包括：
- 耐久度变化率
- Boss掉宝率加成
- 每日任务数量
- 修炼间隔压缩

难度参数表：
    | 参数           | 简单(easy) | 普通(normal) | 困难(hard) |
    | -------------- | ---------- | ------------ | ---------- |
    | 耐久度变化率   | ×0.5       | ×1.0         | ×1.5       |
    | Boss掉宝率加成 | +15%       | +0%          | +30%       |
    | 每日任务数量   | 3          | 5            | 8          |
    | 修炼间隔压缩   | 间隔×0.8   | 标准间隔     | 间隔×1.2   |
"""

from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass


class DifficultyLevel(str, Enum):
    """难度等级枚举"""
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"


@dataclass
class DifficultyParams:
    """难度参数数据结构
    
    Attributes:
        durability_change_rate: 耐久度变化率
        boss_drop_rate_bonus: Boss掉宝率加成
        daily_task_count: 每日任务数量
        review_interval_multiplier: 修炼间隔倍数
    """
    durability_change_rate: float
    boss_drop_rate_bonus: float
    daily_task_count: int
    review_interval_multiplier: float


class DifficultyManager:
    """游戏难度管理器
    
    管理不同难度等级的游戏参数。
    
    Attributes:
        difficulty_params: 难度参数映射
        current_difficulty: 当前难度等级
    """
    
    DEFAULT_DIFFICULTY_PARAMS = {
        DifficultyLevel.EASY: DifficultyParams(
            durability_change_rate=0.5,
            boss_drop_rate_bonus=0.15,
            daily_task_count=3,
            review_interval_multiplier=0.8
        ),
        DifficultyLevel.NORMAL: DifficultyParams(
            durability_change_rate=1.0,
            boss_drop_rate_bonus=0.0,
            daily_task_count=5,
            review_interval_multiplier=1.0
        ),
        DifficultyLevel.HARD: DifficultyParams(
            durability_change_rate=1.5,
            boss_drop_rate_bonus=0.30,
            daily_task_count=8,
            review_interval_multiplier=1.2
        ),
    }
    
    def __init__(
        self, 
        difficulty_params: Optional[Dict[DifficultyLevel, DifficultyParams]] = None,
        current_difficulty: DifficultyLevel = DifficultyLevel.NORMAL
    ):
        """初始化难度管理器
        
        Args:
            difficulty_params: 自定义难度参数映射
            current_difficulty: 当前难度等级
        """
        self.difficulty_params = difficulty_params or self.DEFAULT_DIFFICULTY_PARAMS
        self.current_difficulty = current_difficulty
    
    def get_difficulty_params(self, difficulty: DifficultyLevel) -> DifficultyParams:
        """获取难度参数
        
        Args:
            difficulty: 难度等级
        
        Returns:
            难度参数
        
        Example:
            >>> manager = DifficultyManager()
            >>> params = manager.get_difficulty_params(DifficultyLevel.EASY)
            >>> params.durability_change_rate
            0.5
            >>> params.boss_drop_rate_bonus
            0.15
        """
        return self.difficulty_params.get(difficulty, self.difficulty_params[DifficultyLevel.NORMAL])
    
    def get_current_difficulty_params(self) -> DifficultyParams:
        """获取当前难度的参数
        
        Returns:
            当前难度的参数
        """
        return self.get_difficulty_params(self.current_difficulty)
    
    def set_current_difficulty(self, difficulty: DifficultyLevel):
        """设置当前难度
        
        Args:
            difficulty: 难度等级
        """
        self.current_difficulty = difficulty
    
    def apply_difficulty_multiplier(
        self, 
        base_value: float, 
        param_name: str
    ) -> float:
        """应用难度系数到基础值
        
        Args:
            base_value: 基础值
            param_name: 参数名称（durability_change, boss_drop_rate, review_interval）
        
        Returns:
            应用难度系数后的值
        
        Example:
            >>> manager = DifficultyManager()
            >>> manager.set_current_difficulty(DifficultyLevel.EASY)
            >>> manager.apply_difficulty_multiplier(20, "durability_change")
            10.0  # 20 * 0.5
        """
        params = self.get_current_difficulty_params()
        
        if param_name == "durability_change":
            return base_value * params.durability_change_rate
        elif param_name == "boss_drop_rate":
            return base_value + params.boss_drop_rate_bonus
        elif param_name == "review_interval":
            return base_value * params.review_interval_multiplier
        else:
            return base_value
    
    def get_durability_multiplier(self, difficulty: Optional[DifficultyLevel] = None) -> float:
        """获取耐久度变化率
        
        Args:
            difficulty: 难度等级，默认使用当前难度
        
        Returns:
            耐久度变化率
        """
        if difficulty is None:
            difficulty = self.current_difficulty
        params = self.get_difficulty_params(difficulty)
        return params.durability_change_rate
    
    def get_boss_drop_rate_bonus(self, difficulty: Optional[DifficultyLevel] = None) -> float:
        """获取Boss掉宝率加成
        
        Args:
            difficulty: 难度等级，默认使用当前难度
        
        Returns:
            Boss掉宝率加成
        """
        if difficulty is None:
            difficulty = self.current_difficulty
        params = self.get_difficulty_params(difficulty)
        return params.boss_drop_rate_bonus
    
    def get_daily_task_count(self, difficulty: Optional[DifficultyLevel] = None) -> int:
        """获取每日任务数量
        
        Args:
            difficulty: 难度等级，默认使用当前难度
        
        Returns:
            每日任务数量
        """
        if difficulty is None:
            difficulty = self.current_difficulty
        params = self.get_difficulty_params(difficulty)
        return params.daily_task_count
    
    def get_review_interval_multiplier(self, difficulty: Optional[DifficultyLevel] = None) -> float:
        """获取修炼间隔倍数
        
        Args:
            difficulty: 难度等级，默认使用当前难度
        
        Returns:
            修炼间隔倍数
        """
        if difficulty is None:
            difficulty = self.current_difficulty
        params = self.get_difficulty_params(difficulty)
        return params.review_interval_multiplier
    
    def get_all_difficulty_params(self) -> Dict[str, Dict[str, float]]:
        """获取所有难度参数（字典格式）
        
        Returns:
            难度参数字典
        """
        result = {}
        for level, params in self.difficulty_params.items():
            result[level.value] = {
                "durability_change_rate": params.durability_change_rate,
                "boss_drop_rate_bonus": params.boss_drop_rate_bonus,
                "daily_task_count": params.daily_task_count,
                "review_interval_multiplier": params.review_interval_multiplier,
            }
        return result


def get_difficulty_params(difficulty: str) -> dict:
    """获取难度参数（便捷函数）
    
    Args:
        difficulty: 难度等级（easy/normal/hard）
    
    Returns:
        难度参数字典
    
    Example:
        >>> params = get_difficulty_params("easy")
        >>> params["durability_change_rate"]
        0.5
    """
    manager = DifficultyManager()
    level = DifficultyLevel(difficulty)
    params = manager.get_difficulty_params(level)
    return {
        "durability_change_rate": params.durability_change_rate,
        "boss_drop_rate_bonus": params.boss_drop_rate_bonus,
        "daily_task_count": params.daily_task_count,
        "review_interval_multiplier": params.review_interval_multiplier,
    }


def get_current_difficulty() -> str:
    """获取当前难度（便捷函数）
    
    Returns:
        当前难度等级字符串
    """
    manager = DifficultyManager()
    return manager.current_difficulty.value


def apply_difficulty_multiplier(base_value: float, param_name: str) -> float:
    """应用难度系数到基础值（便捷函数）
    
    Args:
        base_value: 基础值
        param_name: 参数名称
    
    Returns:
        应用难度系数后的值
    """
    manager = DifficultyManager()
    return manager.apply_difficulty_multiplier(base_value, param_name)

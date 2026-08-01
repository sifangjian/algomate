"""
修炼难度参数模块

提供修炼相关的难度参数，包括每日任务数量等。
"""

from enum import Enum
from typing import Optional, Dict
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
        daily_task_count: 每日任务数量
        review_interval_multiplier: 修炼间隔倍数
    """
    daily_task_count: int
    review_interval_multiplier: float


class DifficultyManager:
    """修炼难度管理器

    管理修炼相关的难度参数。

    Attributes:
        difficulty_params: 难度参数映射
        current_difficulty: 当前难度等级
    """

    DEFAULT_DIFFICULTY_PARAMS = {
        DifficultyLevel.EASY: DifficultyParams(
            daily_task_count=3,
            review_interval_multiplier=0.8
        ),
        DifficultyLevel.NORMAL: DifficultyParams(
            daily_task_count=5,
            review_interval_multiplier=1.0
        ),
        DifficultyLevel.HARD: DifficultyParams(
            daily_task_count=8,
            review_interval_multiplier=1.2
        ),
    }

    def __init__(
        self,
        difficulty_params: Optional[Dict[DifficultyLevel, DifficultyParams]] = None,
        current_difficulty: DifficultyLevel = DifficultyLevel.NORMAL
    ):
        self.difficulty_params = difficulty_params or self.DEFAULT_DIFFICULTY_PARAMS
        self.current_difficulty = current_difficulty

    def get_difficulty_params(self, difficulty: DifficultyLevel) -> DifficultyParams:
        return self.difficulty_params.get(difficulty, self.difficulty_params[DifficultyLevel.NORMAL])

    def get_current_difficulty_params(self) -> DifficultyParams:
        return self.get_difficulty_params(self.current_difficulty)

    def set_current_difficulty(self, difficulty: DifficultyLevel):
        self.current_difficulty = difficulty

    def get_daily_task_count(self, difficulty: Optional[DifficultyLevel] = None) -> int:
        if difficulty is None:
            difficulty = self.current_difficulty
        params = self.get_difficulty_params(difficulty)
        return params.daily_task_count

    def get_review_interval_multiplier(self, difficulty: Optional[DifficultyLevel] = None) -> float:
        if difficulty is None:
            difficulty = self.current_difficulty
        params = self.get_difficulty_params(difficulty)
        return params.review_interval_multiplier

    def get_all_difficulty_params(self) -> Dict[str, Dict[str, float]]:
        result = {}
        for level, params in self.difficulty_params.items():
            result[level.value] = {
                "daily_task_count": params.daily_task_count,
                "review_interval_multiplier": params.review_interval_multiplier,
            }
        return result
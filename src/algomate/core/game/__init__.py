"""
游戏核心逻辑模块

包含游戏化修习系统的核心业务逻辑：
- 耐久度管理
- 秘境解锁判断
- 游戏难度参数
"""

from .durability import DurabilityManager, DurabilityAction
from .realm_unlock import RealmUnlockManager, Realm
from .difficulty import DifficultyManager, DifficultyLevel

__all__ = [
    "DurabilityManager",
    "DurabilityAction",
    "RealmUnlockManager",
    "Realm",
    "DifficultyManager",
    "DifficultyLevel",
]

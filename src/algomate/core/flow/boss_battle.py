"""
Boss战流程模块

定义Boss挑战的数据结构，包括：
- 战斗状态枚举
- 战斗会话
- 战斗结果

Boss战业务逻辑已迁移至 algomate.api.routes 中的 boss_router。
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class BattleState(str, Enum):
    """战斗状态枚举"""
    PREPARING = "preparing"
    IN_PROGRESS = "in_progress"
    VICTORY = "victory"
    DEFEAT = "defeat"


@dataclass
class BattleSession:
    """战斗会话数据结构"""
    battle_id: Optional[int]
    boss_id: int
    boss_name: str
    boss_difficulty: str
    card_ids: List[int]
    state: BattleState
    question_id: Optional[int] = None
    attempts: int = 0
    max_attempts: int = 3
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "battle_id": self.battle_id,
            "boss_id": self.boss_id,
            "boss_name": self.boss_name,
            "boss_difficulty": self.boss_difficulty,
            "card_ids": self.card_ids,
            "state": self.state.value,
            "question_id": self.question_id,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class BattleResult:
    """战斗结果数据结构"""
    is_victory: bool
    durability_change: int
    new_card_dropped: bool
    dropped_card: Optional[Dict[str, Any]] = None
    feedback: str = ""
    improvement: str = ""

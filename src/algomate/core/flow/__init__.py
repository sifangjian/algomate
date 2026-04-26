"""
业务流程层

组合多个基础模块实现完整业务流程
"""

from .npc_dialogue import NPCDialogueFlow
from .boss_battle import BossBattleFlow

__all__ = ["NPCDialogueFlow", "BossBattleFlow"]

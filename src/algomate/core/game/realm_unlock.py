"""
秘境解锁判断系统模块

根据用户进度判断秘境是否解锁，包括：
- 秘境解锁条件判断
- 解锁进度计算
- 已解锁秘境列表获取

解锁规则：
    - 新手森林：默认解锁
    - 迷雾沼泽：新手森林熟练度≥60的卡牌 ≥ 3张
    - 智慧圣殿：迷雾沼泽熟练度≥60的卡牌 ≥ 3张
    - 贪婪之塔：智慧圣殿熟练度≥60的卡牌 ≥ 3张
    - 命运迷宫：贪婪之塔熟练度≥60的卡牌 ≥ 3张
    - 分裂山脉：命运迷宫熟练度≥60的卡牌 ≥ 3张
    - 数学殿堂：分裂山脉熟练度≥60的卡牌 ≥ 3张
    - 试炼之地：所有领域熟练度≥60的卡牌 ≥ 5张

熟练度达标定义：耐久度 ≥ 60
"""

from enum import Enum
from typing import Optional, Dict, List
from dataclasses import dataclass


class Realm(str, Enum):
    """秘境枚举"""
    NOVICE_FOREST = "新手森林"
    MIST_SWAMP = "迷雾沼泽"
    WISDOM_TEMPLE = "智慧圣殿"
    GREED_TOWER = "贪婪之塔"
    FATE_MAZE = "命运迷宫"
    SPLIT_MOUNTAIN = "分裂山脉"
    MATH_HALL = "数学殿堂"
    TRIAL_LAND = "试炼之地"


@dataclass
class UnlockCondition:
    """解锁条件数据结构
    
    Attributes:
        realm: 秘境名称
        required_realm: 需要的前置秘境
        required_count: 需要的达标卡牌数量
        mastery_threshold: 熟练度阈值
        is_default_unlocked: 是否默认解锁
    """
    realm: str
    required_realm: Optional[str]
    required_count: int
    mastery_threshold: int = 60
    is_default_unlocked: bool = False


@dataclass
class RealmProgress:
    """秘境进度数据结构
    
    Attributes:
        realm: 秘境名称
        required: 需要的达标卡牌数量
        current: 当前的达标卡牌数量
        unlocked: 是否已解锁
        progress_percentage: 进度百分比
    """
    realm: str
    required: int
    current: int
    unlocked: bool
    progress_percentage: float


class RealmUnlockManager:
    """秘境解锁管理器
    
    管理秘境的解锁状态和进度计算。
    
    Attributes:
        unlock_conditions: 解锁条件映射
        mastery_threshold: 熟练度阈值（耐久度）
    """
    
    DEFAULT_UNLOCK_CONDITIONS = {
        Realm.NOVICE_FOREST: UnlockCondition(
            realm=Realm.NOVICE_FOREST.value,
            required_realm=None,
            required_count=0,
            is_default_unlocked=True
        ),
        Realm.MIST_SWAMP: UnlockCondition(
            realm=Realm.MIST_SWAMP.value,
            required_realm=Realm.NOVICE_FOREST.value,
            required_count=3,
            mastery_threshold=60
        ),
        Realm.WISDOM_TEMPLE: UnlockCondition(
            realm=Realm.WISDOM_TEMPLE.value,
            required_realm=Realm.MIST_SWAMP.value,
            required_count=3,
            mastery_threshold=60
        ),
        Realm.GREED_TOWER: UnlockCondition(
            realm=Realm.GREED_TOWER.value,
            required_realm=Realm.WISDOM_TEMPLE.value,
            required_count=3,
            mastery_threshold=60
        ),
        Realm.FATE_MAZE: UnlockCondition(
            realm=Realm.FATE_MAZE.value,
            required_realm=Realm.GREED_TOWER.value,
            required_count=3,
            mastery_threshold=60
        ),
        Realm.SPLIT_MOUNTAIN: UnlockCondition(
            realm=Realm.SPLIT_MOUNTAIN.value,
            required_realm=Realm.FATE_MAZE.value,
            required_count=3,
            mastery_threshold=60
        ),
        Realm.MATH_HALL: UnlockCondition(
            realm=Realm.MATH_HALL.value,
            required_realm=Realm.SPLIT_MOUNTAIN.value,
            required_count=3,
            mastery_threshold=60
        ),
        Realm.TRIAL_LAND: UnlockCondition(
            realm=Realm.TRIAL_LAND.value,
            required_realm=None,
            required_count=5,
            mastery_threshold=60
        ),
    }
    
    def __init__(
        self, 
        unlock_conditions: Optional[Dict[Realm, UnlockCondition]] = None,
        mastery_threshold: int = 60
    ):
        """初始化秘境解锁管理器
        
        Args:
            unlock_conditions: 自定义解锁条件映射
            mastery_threshold: 熟练度阈值（耐久度）
        """
        self.unlock_conditions = unlock_conditions or self.DEFAULT_UNLOCK_CONDITIONS
        self.mastery_threshold = mastery_threshold
    
    def count_mastered_cards(self, cards: list, domain: str) -> int:
        """统计指定领域的达标卡牌数量
        
        Args:
            cards: 卡牌列表
            domain: 领域名称
        
        Returns:
            达标卡牌数量
        
        Note:
            达标定义：耐久度 ≥ mastery_threshold 且未封印
        """
        count = 0
        for card in cards:
            if hasattr(card, 'domain') and card.domain == domain:
                durability = getattr(card, 'durability', 0)
                is_sealed = getattr(card, 'is_sealed', False)
                if durability >= self.mastery_threshold and not is_sealed:
                    count += 1
        return count
    
    def count_all_mastered_cards(self, cards: list) -> int:
        """统计所有领域的达标卡牌数量
        
        Args:
            cards: 卡牌列表
        
        Returns:
            达标卡牌总数
        """
        count = 0
        for card in cards:
            durability = getattr(card, 'durability', 0)
            is_sealed = getattr(card, 'is_sealed', False)
            if durability >= self.mastery_threshold and not is_sealed:
                count += 1
        return count
    
    def check_realm_unlock(
        self, 
        realm: Realm, 
        cards: list,
        unlocked_realms: Optional[List[str]] = None
    ) -> bool:
        """检查指定秘境是否解锁
        
        Args:
            realm: 秘境枚举
            cards: 卡牌列表
            unlocked_realms: 已解锁秘境列表（用于依赖判断）
        
        Returns:
            是否已解锁
        
        Example:
            >>> manager = RealmUnlockManager()
            >>> cards = [...]  # 卡牌列表
            >>> manager.check_realm_unlock(Realm.NOVICE_FOREST, cards)
            True  # 新手森林默认解锁
        """
        condition = self.unlock_conditions.get(realm)
        if not condition:
            return False
        
        if condition.is_default_unlocked:
            return True
        
        if realm == Realm.TRIAL_LAND:
            mastered_count = self.count_all_mastered_cards(cards)
            return mastered_count >= condition.required_count
        
        if not condition.required_realm:
            return False
        
        if unlocked_realms is None:
            unlocked_realms = self.get_unlocked_realms(cards)
        
        if condition.required_realm not in unlocked_realms:
            return False
        
        mastered_count = self.count_mastered_cards(cards, condition.required_realm)
        return mastered_count >= condition.required_count
    
    def get_unlocked_realms(self, cards: list) -> List[str]:
        """获取所有已解锁秘境列表
        
        Args:
            cards: 卡牌列表
        
        Returns:
            已解锁秘境名称列表
        
        Example:
            >>> manager = RealmUnlockManager()
            >>> cards = [...]  # 卡牌列表
            >>> unlocked = manager.get_unlocked_realms(cards)
            >>> print(unlocked)
            ['新手森林', '迷雾沼泽']
        """
        unlocked = []
        
        for realm in Realm:
            if self.check_realm_unlock(realm, cards, unlocked):
                unlocked.append(realm.value)
        
        return unlocked
    
    def get_realm_progress(self, realm: Realm, cards: list) -> RealmProgress:
        """获取秘境解锁进度
        
        Args:
            realm: 秘境枚举
            cards: 卡牌列表
        
        Returns:
            RealmProgress 包含进度详情
        
        Example:
            >>> manager = RealmUnlockManager()
            >>> cards = [...]  # 卡牌列表
            >>> progress = manager.get_realm_progress(Realm.MIST_SWAMP, cards)
            >>> print(progress)
            RealmProgress(realm='迷雾沼泽', required=3, current=1, unlocked=False, progress_percentage=33.33)
        """
        condition = self.unlock_conditions.get(realm)
        if not condition:
            return RealmProgress(
                realm=realm.value,
                required=0,
                current=0,
                unlocked=False,
                progress_percentage=0.0
            )
        
        if condition.is_default_unlocked:
            return RealmProgress(
                realm=realm.value,
                required=0,
                current=0,
                unlocked=True,
                progress_percentage=100.0
            )
        
        if realm == Realm.TRIAL_LAND:
            current = self.count_all_mastered_cards(cards)
        else:
            current = self.count_mastered_cards(cards, condition.required_realm) if condition.required_realm else 0
        
        unlocked = self.check_realm_unlock(realm, cards)
        
        progress_percentage = min(100.0, (current / condition.required_count * 100)) if condition.required_count > 0 else 0.0
        
        return RealmProgress(
            realm=realm.value,
            required=condition.required_count,
            current=current,
            unlocked=unlocked,
            progress_percentage=round(progress_percentage, 2)
        )
    
    def get_next_unlockable_realm(self, cards: list) -> Optional[str]:
        """获取下一个可解锁的秘境
        
        Args:
            cards: 卡牌列表
        
        Returns:
            下一个可解锁的秘境名称，如果全部解锁则返回 None
        
        Example:
            >>> manager = RealmUnlockManager()
            >>> cards = [...]  # 卡牌列表
            >>> next_realm = manager.get_next_unlockable_realm(cards)
            >>> print(next_realm)
            '迷雾沼泽'
        """
        unlocked_realms = self.get_unlocked_realms(cards)
        
        for realm in Realm:
            if realm.value not in unlocked_realms:
                return realm.value
        
        return None
    
    def get_all_realms_progress(self, cards: list) -> Dict[str, RealmProgress]:
        """获取所有秘境的解锁进度
        
        Args:
            cards: 卡牌列表
        
        Returns:
            秘境名称到进度的映射
        """
        progress_dict = {}
        for realm in Realm:
            progress_dict[realm.value] = self.get_realm_progress(realm, cards)
        return progress_dict


def check_realm_unlock(realm: str, cards: list) -> bool:
    """检查指定秘境是否解锁（便捷函数）
    
    Args:
        realm: 秘境名称
        cards: 卡牌列表
    
    Returns:
        是否已解锁
    """
    manager = RealmUnlockManager()
    realm_enum = Realm(realm)
    return manager.check_realm_unlock(realm_enum, cards)


def get_unlocked_realms(cards: list) -> List[str]:
    """获取所有已解锁秘境列表（便捷函数）
    
    Args:
        cards: 卡牌列表
    
    Returns:
        已解锁秘境名称列表
    """
    manager = RealmUnlockManager()
    return manager.get_unlocked_realms(cards)


def get_realm_progress(realm: str, cards: list) -> dict:
    """获取秘境解锁进度（便捷函数）
    
    Args:
        realm: 秘境名称
        cards: 卡牌列表
    
    Returns:
        进度字典
    """
    manager = RealmUnlockManager()
    realm_enum = Realm(realm)
    progress = manager.get_realm_progress(realm_enum, cards)
    return {
        "realm": progress.realm,
        "required": progress.required,
        "current": progress.current,
        "unlocked": progress.unlocked,
        "progress_percentage": progress.progress_percentage,
    }


def get_next_unlockable_realm(cards: list) -> Optional[str]:
    """获取下一个可解锁的秘境（便捷函数）
    
    Args:
        cards: 卡牌列表
    
    Returns:
        下一个可解锁的秘境名称
    """
    manager = RealmUnlockManager()
    return manager.get_next_unlockable_realm(cards)

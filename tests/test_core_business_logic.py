"""
M3 核心业务逻辑层单元测试

测试覆盖：
- M3.1 遗忘曲线引擎
- M3.2 耐久度管理系统
- M3.3 秘境解锁判断系统
- M3.4 游戏难度参数系统
"""

import sys
import pytest
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from algomate.core.memory.forgotten_curve import (
    ForgottenCurveEngine,
    ReviewAction,
    ReviewResult,
    calculate_next_review,
    should_review,
    get_review_interval,
    get_daily_review_tasks,
)

from algomate.core.game.durability import (
    DurabilityManager,
    DurabilityAction,
    DurabilityConfig,
    update_durability,
    get_critical_cards,
    unseal_card,
)

from algomate.core.game.realm_unlock import (
    RealmUnlockManager,
    Realm,
    UnlockCondition,
    RealmProgress,
    check_realm_unlock,
    get_unlocked_realms,
    get_realm_progress,
    get_next_unlockable_realm,
)

from algomate.core.game.difficulty import (
    DifficultyManager,
    DifficultyLevel,
    DifficultyParams,
    get_difficulty_params,
    get_current_difficulty,
    apply_difficulty_multiplier,
)


@dataclass
class MockCard:
    """模拟卡牌对象"""
    id: int
    name: str
    domain: str
    durability: int
    created_at: datetime
    last_reviewed: datetime = None
    review_level: int = 0
    is_sealed: bool = False


class TestForgottenCurveEngine:
    """遗忘曲线引擎测试"""
    
    def test_get_review_interval(self):
        """测试获取修炼间隔"""
        engine = ForgottenCurveEngine()
        
        assert engine.get_review_interval(0) == 0
        assert engine.get_review_interval(1) == 1
        assert engine.get_review_interval(2) == 3
        assert engine.get_review_interval(3) == 7
        assert engine.get_review_interval(4) == 14
        assert engine.get_review_interval(5) == 30
        assert engine.get_review_interval(6) == 60
    
    def test_get_review_interval_invalid_level(self):
        """测试无效修炼等级"""
        engine = ForgottenCurveEngine()
        
        with pytest.raises(ValueError):
            engine.get_review_interval(-1)
        
        with pytest.raises(ValueError):
            engine.get_review_interval(7)
    
    def test_calculate_next_review_success(self):
        """测试修炼成功后的下次修炼时间"""
        engine = ForgottenCurveEngine()
        last_reviewed = datetime(2024, 1, 1, 10, 0)
        
        next_review, new_level = engine.calculate_next_review(
            last_reviewed, 1, ReviewAction.SUCCESS
        )
        
        assert new_level == 2
        assert next_review == last_reviewed + timedelta(days=3)
    
    def test_calculate_next_review_fail(self):
        """测试修炼失败后的下次修炼时间"""
        engine = ForgottenCurveEngine()
        last_reviewed = datetime(2024, 1, 1, 10, 0)
        
        next_review, new_level = engine.calculate_next_review(
            last_reviewed, 2, ReviewAction.FAIL
        )
        
        assert new_level == 1
        assert next_review == last_reviewed + timedelta(days=1)
    
    def test_calculate_next_review_max_level(self):
        """测试最高等级修炼成功"""
        engine = ForgottenCurveEngine()
        last_reviewed = datetime(2024, 1, 1, 10, 0)
        
        next_review, new_level = engine.calculate_next_review(
            last_reviewed, 6, ReviewAction.SUCCESS
        )
        
        assert new_level == 6
    
    def test_calculate_next_review_min_level(self):
        """测试最低等级修炼失败"""
        engine = ForgottenCurveEngine()
        last_reviewed = datetime(2024, 1, 1, 10, 0)
        
        next_review, new_level = engine.calculate_next_review(
            last_reviewed, 0, ReviewAction.FAIL
        )
        
        assert new_level == 0
    
    def test_should_review_never_reviewed(self):
        """测试从未修炼的卡牌"""
        engine = ForgottenCurveEngine()
        created_at = datetime.now() - timedelta(days=2)
        
        assert engine.should_review(created_at, None, 0) is True
    
    def test_should_review_recently_reviewed(self):
        """测试刚修炼过的卡牌"""
        engine = ForgottenCurveEngine()
        created_at = datetime(2024, 1, 1, 10, 0)
        last_reviewed = datetime.now() - timedelta(hours=12)
        
        assert engine.should_review(created_at, last_reviewed, 1) is False
    
    def test_get_daily_review_tasks(self):
        """测试获取今日修炼任务"""
        engine = ForgottenCurveEngine()
        
        cards = [
            MockCard(
                id=1,
                name="卡牌1",
                domain="新手森林",
                durability=80,
                created_at=datetime.now() - timedelta(days=2),
                last_reviewed=None,
                review_level=0,
            ),
            MockCard(
                id=2,
                name="卡牌2",
                domain="新手森林",
                durability=90,
                created_at=datetime.now() - timedelta(hours=12),
                last_reviewed=datetime.now() - timedelta(hours=6),
                review_level=1,
            ),
            MockCard(
                id=3,
                name="卡牌3",
                domain="新手森林",
                durability=20,
                created_at=datetime.now() - timedelta(days=5),
                last_reviewed=None,
                review_level=0,
                is_sealed=True,
            ),
        ]
        
        due_cards = engine.get_daily_review_tasks(cards)
        
        assert len(due_cards) == 1
        assert due_cards[0].id == 1
    
    def test_convenience_functions(self):
        """测试便捷函数"""
        last_reviewed = datetime(2024, 1, 1, 10, 0)
        
        next_review, new_level = calculate_next_review(last_reviewed, 1, ReviewAction.SUCCESS)
        assert new_level == 2
        
        interval = get_review_interval(3)
        assert interval == 7


class TestDurabilityManager:
    """耐久度管理系统测试"""
    
    def test_get_difficulty_multiplier(self):
        """测试获取难度系数"""
        manager = DurabilityManager()
        
        assert manager.get_difficulty_multiplier("easy") == 0.5
        assert manager.get_difficulty_multiplier("normal") == 1.0
        assert manager.get_difficulty_multiplier("hard") == 1.5
    
    def test_calculate_durability_change_success(self):
        """测试修炼成功的耐久度变化"""
        manager = DurabilityManager()
        
        change = manager.calculate_durability_change(
            DurabilityAction.REVIEW_SUCCESS, "normal"
        )
        assert change == 20
        
        change = manager.calculate_durability_change(
            DurabilityAction.REVIEW_SUCCESS, "easy"
        )
        assert change == 10
        
        change = manager.calculate_durability_change(
            DurabilityAction.REVIEW_SUCCESS, "hard"
        )
        assert change == 30
    
    def test_calculate_durability_change_fail(self):
        """测试修炼失败的耐久度变化"""
        manager = DurabilityManager()
        
        change = manager.calculate_durability_change(
            DurabilityAction.REVIEW_FAIL, "normal"
        )
        assert change == -5
        
        change = manager.calculate_durability_change(
            DurabilityAction.REVIEW_FAIL, "easy"
        )
        assert change == -2
        
        change = manager.calculate_durability_change(
            DurabilityAction.REVIEW_FAIL, "hard"
        )
        assert change == -7
    
    def test_calculate_durability_change_daily_decay(self):
        """测试每日衰减的耐久度变化"""
        manager = DurabilityManager()
        
        change = manager.calculate_durability_change(
            DurabilityAction.DAILY_DECAY, "normal"
        )
        assert change == -2
        
        change = manager.calculate_durability_change(
            DurabilityAction.DAILY_DECAY, "easy"
        )
        assert change == -1
        
        change = manager.calculate_durability_change(
            DurabilityAction.DAILY_DECAY, "hard"
        )
        assert change == -3
    
    def test_update_durability_success(self):
        """测试更新耐久度（成功）"""
        manager = DurabilityManager()
        
        new_dur, is_critical, is_sealed = manager.update_durability(
            80, DurabilityAction.REVIEW_SUCCESS, "normal"
        )
        
        assert new_dur == 100
        assert is_critical is False
        assert is_sealed is False
    
    def test_update_durability_fail(self):
        """测试更新耐久度（失败）"""
        manager = DurabilityManager()
        
        new_dur, is_critical, is_sealed = manager.update_durability(
            30, DurabilityAction.REVIEW_FAIL, "normal"
        )
        
        assert new_dur == 25
        assert is_critical is True
        assert is_sealed is False
    
    def test_update_durability_sealed(self):
        """测试更新耐久度（封印）"""
        manager = DurabilityManager()
        
        new_dur, is_critical, is_sealed = manager.update_durability(
            2, DurabilityAction.REVIEW_FAIL, "normal"
        )
        
        assert new_dur == 0
        assert is_critical is True
        assert is_sealed is True
    
    def test_is_critical(self):
        """测试濒危判断"""
        manager = DurabilityManager()
        
        assert manager.is_critical(29) is True
        assert manager.is_critical(30) is False
        assert manager.is_critical(50) is False
    
    def test_is_sealed(self):
        """测试封印判断"""
        manager = DurabilityManager()
        
        assert manager.is_sealed(0) is True
        assert manager.is_sealed(1) is False
    
    def test_unseal_durability(self):
        """测试解封耐久度"""
        manager = DurabilityManager()
        
        unseal_dur = manager.unseal_durability()
        assert unseal_dur == 30
    
    def test_convenience_functions(self):
        """测试便捷函数"""
        new_dur, is_critical, is_sealed = update_durability(
            80, DurabilityAction.REVIEW_SUCCESS, "normal"
        )
        assert new_dur == 100
        
        cards = [
            MockCard(id=1, name="卡牌1", domain="新手森林", durability=20, created_at=datetime.now()),
            MockCard(id=2, name="卡牌2", domain="新手森林", durability=50, created_at=datetime.now()),
        ]
        critical = get_critical_cards(cards)
        assert len(critical) == 1
        
        unseal_dur = unseal_card(0)
        assert unseal_dur == 30


class TestRealmUnlockManager:
    """秘境解锁判断系统测试"""
    
    def test_count_mastered_cards(self):
        """测试统计达标卡牌"""
        manager = RealmUnlockManager()
        
        cards = [
            MockCard(id=1, name="卡牌1", domain="新手森林", durability=70, created_at=datetime.now()),
            MockCard(id=2, name="卡牌2", domain="新手森林", durability=50, created_at=datetime.now()),
            MockCard(id=3, name="卡牌3", domain="新手森林", durability=80, created_at=datetime.now()),
            MockCard(id=4, name="卡牌4", domain="迷雾沼泽", durability=90, created_at=datetime.now()),
        ]
        
        count = manager.count_mastered_cards(cards, "新手森林")
        assert count == 2
    
    def test_count_all_mastered_cards(self):
        """测试统计所有领域达标卡牌"""
        manager = RealmUnlockManager()
        
        cards = [
            MockCard(id=1, name="卡牌1", domain="新手森林", durability=70, created_at=datetime.now()),
            MockCard(id=2, name="卡牌2", domain="迷雾沼泽", durability=80, created_at=datetime.now()),
            MockCard(id=3, name="卡牌3", domain="智慧圣殿", durability=50, created_at=datetime.now()),
        ]
        
        count = manager.count_all_mastered_cards(cards)
        assert count == 2
    
    def test_check_realm_unlock_default(self):
        """测试默认解锁的秘境"""
        manager = RealmUnlockManager()
        cards = []
        
        assert manager.check_realm_unlock(Realm.NOVICE_FOREST, cards) is True
    
    def test_check_realm_unlock_locked(self):
        """测试未解锁的秘境"""
        manager = RealmUnlockManager()
        
        cards = [
            MockCard(id=1, name="卡牌1", domain="新手森林", durability=50, created_at=datetime.now()),
        ]
        
        assert manager.check_realm_unlock(Realm.MIST_SWAMP, cards) is False
    
    def test_check_realm_unlock_unlocked(self):
        """测试已解锁的秘境"""
        manager = RealmUnlockManager()
        
        cards = [
            MockCard(id=1, name="卡牌1", domain="新手森林", durability=70, created_at=datetime.now()),
            MockCard(id=2, name="卡牌2", domain="新手森林", durability=80, created_at=datetime.now()),
            MockCard(id=3, name="卡牌3", domain="新手森林", durability=90, created_at=datetime.now()),
        ]
        
        assert manager.check_realm_unlock(Realm.MIST_SWAMP, cards) is True
    
    def test_get_unlocked_realms(self):
        """测试获取已解锁秘境列表"""
        manager = RealmUnlockManager()
        
        cards = [
            MockCard(id=1, name="卡牌1", domain="新手森林", durability=70, created_at=datetime.now()),
            MockCard(id=2, name="卡牌2", domain="新手森林", durability=80, created_at=datetime.now()),
            MockCard(id=3, name="卡牌3", domain="新手森林", durability=90, created_at=datetime.now()),
        ]
        
        unlocked = manager.get_unlocked_realms(cards)
        assert "新手森林" in unlocked
        assert "迷雾沼泽" in unlocked
    
    def test_get_realm_progress(self):
        """测试获取秘境进度"""
        manager = RealmUnlockManager()
        
        cards = [
            MockCard(id=1, name="卡牌1", domain="新手森林", durability=70, created_at=datetime.now()),
            MockCard(id=2, name="卡牌2", domain="新手森林", durability=80, created_at=datetime.now()),
        ]
        
        progress = manager.get_realm_progress(Realm.MIST_SWAMP, cards)
        
        assert progress.realm == "迷雾沼泽"
        assert progress.required == 3
        assert progress.current == 2
        assert progress.unlocked is False
        assert progress.progress_percentage == 66.67
    
    def test_get_next_unlockable_realm(self):
        """测试获取下一个可解锁秘境"""
        manager = RealmUnlockManager()
        
        cards = []
        next_realm = manager.get_next_unlockable_realm(cards)
        assert next_realm == "迷雾沼泽"
    
    def test_convenience_functions(self):
        """测试便捷函数"""
        cards = [
            MockCard(id=1, name="卡牌1", domain="新手森林", durability=70, created_at=datetime.now()),
        ]
        
        unlocked = check_realm_unlock("新手森林", cards)
        assert unlocked is True
        
        unlocked_list = get_unlocked_realms(cards)
        assert "新手森林" in unlocked_list
        
        progress = get_realm_progress("迷雾沼泽", cards)
        assert progress["required"] == 3


class TestDifficultyManager:
    """游戏难度参数系统测试"""
    
    def test_get_difficulty_params(self):
        """测试获取难度参数"""
        manager = DifficultyManager()
        
        easy_params = manager.get_difficulty_params(DifficultyLevel.EASY)
        assert easy_params.durability_change_rate == 0.5
        assert easy_params.boss_drop_rate_bonus == 0.15
        assert easy_params.daily_task_count == 3
        assert easy_params.review_interval_multiplier == 0.8
        
        normal_params = manager.get_difficulty_params(DifficultyLevel.NORMAL)
        assert normal_params.durability_change_rate == 1.0
        assert normal_params.boss_drop_rate_bonus == 0.0
        assert normal_params.daily_task_count == 5
        assert normal_params.review_interval_multiplier == 1.0
        
        hard_params = manager.get_difficulty_params(DifficultyLevel.HARD)
        assert hard_params.durability_change_rate == 1.5
        assert hard_params.boss_drop_rate_bonus == 0.30
        assert hard_params.daily_task_count == 8
        assert hard_params.review_interval_multiplier == 1.2
    
    def test_set_current_difficulty(self):
        """测试设置当前难度"""
        manager = DifficultyManager()
        
        manager.set_current_difficulty(DifficultyLevel.HARD)
        assert manager.current_difficulty == DifficultyLevel.HARD
        
        params = manager.get_current_difficulty_params()
        assert params.durability_change_rate == 1.5
    
    def test_apply_difficulty_multiplier(self):
        """测试应用难度系数"""
        manager = DifficultyManager()
        
        manager.set_current_difficulty(DifficultyLevel.EASY)
        
        result = manager.apply_difficulty_multiplier(20, "durability_change")
        assert result == 10.0
        
        result = manager.apply_difficulty_multiplier(0.5, "boss_drop_rate")
        assert result == 0.65
        
        result = manager.apply_difficulty_multiplier(10, "review_interval")
        assert result == 8.0
    
    def test_get_durability_multiplier(self):
        """测试获取耐久度变化率"""
        manager = DifficultyManager()
        
        assert manager.get_durability_multiplier(DifficultyLevel.EASY) == 0.5
        assert manager.get_durability_multiplier(DifficultyLevel.NORMAL) == 1.0
        assert manager.get_durability_multiplier(DifficultyLevel.HARD) == 1.5
    
    def test_get_boss_drop_rate_bonus(self):
        """测试获取Boss掉宝率加成"""
        manager = DifficultyManager()
        
        assert manager.get_boss_drop_rate_bonus(DifficultyLevel.EASY) == 0.15
        assert manager.get_boss_drop_rate_bonus(DifficultyLevel.NORMAL) == 0.0
        assert manager.get_boss_drop_rate_bonus(DifficultyLevel.HARD) == 0.30
    
    def test_get_daily_task_count(self):
        """测试获取每日任务数量"""
        manager = DifficultyManager()
        
        assert manager.get_daily_task_count(DifficultyLevel.EASY) == 3
        assert manager.get_daily_task_count(DifficultyLevel.NORMAL) == 5
        assert manager.get_daily_task_count(DifficultyLevel.HARD) == 8
    
    def test_get_review_interval_multiplier(self):
        """测试获取修炼间隔倍数"""
        manager = DifficultyManager()
        
        assert manager.get_review_interval_multiplier(DifficultyLevel.EASY) == 0.8
        assert manager.get_review_interval_multiplier(DifficultyLevel.NORMAL) == 1.0
        assert manager.get_review_interval_multiplier(DifficultyLevel.HARD) == 1.2
    
    def test_get_all_difficulty_params(self):
        """测试获取所有难度参数"""
        manager = DifficultyManager()
        
        all_params = manager.get_all_difficulty_params()
        
        assert "easy" in all_params
        assert "normal" in all_params
        assert "hard" in all_params
        
        assert all_params["easy"]["durability_change_rate"] == 0.5
        assert all_params["normal"]["durability_change_rate"] == 1.0
        assert all_params["hard"]["durability_change_rate"] == 1.5
    
    def test_convenience_functions(self):
        """测试便捷函数"""
        params = get_difficulty_params("easy")
        assert params["durability_change_rate"] == 0.5
        
        current = get_current_difficulty()
        assert current == "normal"
        
        result = apply_difficulty_multiplier(20, "durability_change")
        assert result == 20.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

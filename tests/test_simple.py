"""
M3 核心业务逻辑层简单测试脚本

不依赖 pytest，直接测试核心功能
"""

import sys
import os
from datetime import datetime, timedelta
from dataclasses import dataclass

sys.path.insert(0, "f:\\workspace\\python\\algomate\\src")

os.environ['PYTHONIOENCODING'] = 'utf-8'

from algomate.core.memory.forgotten_curve import (
    ForgottenCurveEngine,
    ReviewAction,
    calculate_next_review,
    get_review_interval,
)

from algomate.core.game.durability import (
    DurabilityManager,
    DurabilityAction,
    update_durability,
)

from algomate.core.game.realm_unlock import (
    RealmUnlockManager,
    Realm,
    check_realm_unlock,
)

from algomate.core.game.difficulty import (
    DifficultyManager,
    DifficultyLevel,
    get_difficulty_params,
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


def test_forgotten_curve():
    """测试遗忘曲线引擎"""
    print("=" * 60)
    print("测试 M3.1 遗忘曲线引擎")
    print("=" * 60)
    
    engine = ForgottenCurveEngine()
    
    print("\n1. 测试获取修炼间隔")
    assert engine.get_review_interval(0) == 0, "修炼等级0失败"
    print("   [OK] 修炼等级0: 间隔0天")
    
    assert engine.get_review_interval(1) == 1, "修炼等级1失败"
    print("   [OK] 修炼等级1: 间隔1天")
    
    assert engine.get_review_interval(3) == 7, "修炼等级3失败"
    print("   [OK] 修炼等级3: 间隔7天")
    
    print("\n2. 测试修炼成功后的下次修炼时间")
    last_reviewed = datetime(2024, 1, 1, 10, 0)
    next_review, new_level = engine.calculate_next_review(
        last_reviewed, 1, ReviewAction.SUCCESS
    )
    assert new_level == 2, "修炼成功等级提升失败"
    print(f"   [OK] 修炼成功: 等级从1提升到{new_level}")
    
    print("\n3. 测试修炼失败后的下次修炼时间")
    next_review, new_level = engine.calculate_next_review(
        last_reviewed, 2, ReviewAction.FAIL
    )
    assert new_level == 1, "修炼失败等级下降失败"
    print(f"   [OK] 修炼失败: 等级从2下降到{new_level}")
    
    print("\n[OK] M3.1 遗忘曲线引擎测试通过")


def test_durability():
    """测试耐久度管理系统"""
    print("\n" + "=" * 60)
    print("测试 M3.2 耐久度管理系统")
    print("=" * 60)
    
    manager = DurabilityManager()
    
    print("\n1. 测试获取难度系数")
    assert manager.get_difficulty_multiplier("easy") == 0.5, "简单难度系数失败"
    print("   [OK] 简单难度系数: 0.5")
    
    assert manager.get_difficulty_multiplier("normal") == 1.0, "普通难度系数失败"
    print("   [OK] 普通难度系数: 1.0")
    
    assert manager.get_difficulty_multiplier("hard") == 1.5, "困难难度系数失败"
    print("   [OK] 困难难度系数: 1.5")
    
    print("\n2. 测试修炼成功的耐久度变化")
    change = manager.calculate_durability_change(
        DurabilityAction.REVIEW_SUCCESS, "normal"
    )
    assert change == 20, "修炼成功耐久度变化失败"
    print(f"   [OK] 修炼成功(普通): +{change}")
    
    print("\n3. 测试修炼失败的耐久度变化")
    change = manager.calculate_durability_change(
        DurabilityAction.REVIEW_FAIL, "normal"
    )
    assert change == -5, "修炼失败耐久度变化失败"
    print(f"   [OK] 修炼失败(普通): {change}")
    
    print("\n4. 测试更新耐久度")
    new_dur, is_critical, is_sealed = manager.update_durability(
        80, DurabilityAction.REVIEW_SUCCESS, "normal"
    )
    assert new_dur == 100, "更新耐久度失败"
    print(f"   [OK] 更新耐久度: 80 -> {new_dur}")
    
    print("\n5. 测试濒危判断")
    assert manager.is_critical(29) is True, "濒危判断失败"
    print("   [OK] 耐久度29: 濒危")
    
    assert manager.is_critical(30) is False, "濒危判断失败"
    print("   [OK] 耐久度30: 正常")
    
    print("\n[OK] M3.2 耐久度管理系统测试通过")


def test_realm_unlock():
    """测试秘境解锁判断系统"""
    print("\n" + "=" * 60)
    print("测试 M3.3 秘境解锁判断系统")
    print("=" * 60)
    
    manager = RealmUnlockManager()
    
    print("\n1. 测试默认解锁的秘境")
    cards = []
    assert manager.check_realm_unlock(Realm.NOVICE_FOREST, cards) is True, "新手森林默认解锁失败"
    print("   [OK] 新手森林: 默认解锁")
    
    print("\n2. 测试统计达标卡牌")
    cards = [
        MockCard(id=1, name="卡牌1", domain="新手森林", durability=70, created_at=datetime.now()),
        MockCard(id=2, name="卡牌2", domain="新手森林", durability=50, created_at=datetime.now()),
        MockCard(id=3, name="卡牌3", domain="新手森林", durability=80, created_at=datetime.now()),
    ]
    count = manager.count_mastered_cards(cards, "新手森林")
    assert count == 2, "统计达标卡牌失败"
    print(f"   [OK] 新手森林达标卡牌: {count}张")
    
    print("\n3. 测试秘境解锁判断")
    unlocked = manager.check_realm_unlock(Realm.MIST_SWAMP, cards)
    assert unlocked is False, "秘境解锁判断失败"
    print(f"   [OK] 迷雾沼泽: 未解锁 (需要3张，当前2张)")
    
    print("\n4. 测试获取已解锁秘境列表")
    unlocked_list = manager.get_unlocked_realms(cards)
    assert "新手森林" in unlocked_list, "获取已解锁秘境失败"
    print(f"   [OK] 已解锁秘境: {unlocked_list}")
    
    print("\n5. 测试获取秘境进度")
    progress = manager.get_realm_progress(Realm.MIST_SWAMP, cards)
    assert progress.required == 3, "获取秘境进度失败"
    assert progress.current == 2, "获取秘境进度失败"
    print(f"   [OK] 迷雾沼泽进度: {progress.current}/{progress.required}")
    
    print("\n[OK] M3.3 秘境解锁判断系统测试通过")


def test_difficulty():
    """测试游戏难度参数系统"""
    print("\n" + "=" * 60)
    print("测试 M3.4 游戏难度参数系统")
    print("=" * 60)
    
    manager = DifficultyManager()
    
    print("\n1. 测试获取难度参数")
    easy_params = manager.get_difficulty_params(DifficultyLevel.EASY)
    assert easy_params.durability_change_rate == 0.5, "简单难度参数失败"
    print(f"   [OK] 简单难度: 耐久度变化率={easy_params.durability_change_rate}")
    
    normal_params = manager.get_difficulty_params(DifficultyLevel.NORMAL)
    assert normal_params.durability_change_rate == 1.0, "普通难度参数失败"
    print(f"   [OK] 普通难度: 耐久度变化率={normal_params.durability_change_rate}")
    
    hard_params = manager.get_difficulty_params(DifficultyLevel.HARD)
    assert hard_params.durability_change_rate == 1.5, "困难难度参数失败"
    print(f"   [OK] 困难难度: 耐久度变化率={hard_params.durability_change_rate}")
    
    print("\n2. 测试Boss掉宝率加成")
    assert manager.get_boss_drop_rate_bonus(DifficultyLevel.EASY) == 0.15, "Boss掉宝率失败"
    print(f"   [OK] 简单难度: Boss掉宝率加成=+15%")
    
    assert manager.get_boss_drop_rate_bonus(DifficultyLevel.HARD) == 0.30, "Boss掉宝率失败"
    print(f"   [OK] 困难难度: Boss掉宝率加成=+30%")
    
    print("\n3. 测试每日任务数量")
    assert manager.get_daily_task_count(DifficultyLevel.EASY) == 3, "每日任务数量失败"
    print(f"   [OK] 简单难度: 每日任务=3个")
    
    assert manager.get_daily_task_count(DifficultyLevel.NORMAL) == 5, "每日任务数量失败"
    print(f"   [OK] 普通难度: 每日任务=5个")
    
    assert manager.get_daily_task_count(DifficultyLevel.HARD) == 8, "每日任务数量失败"
    print(f"   [OK] 困难难度: 每日任务=8个")
    
    print("\n4. 测试应用难度系数")
    manager.set_current_difficulty(DifficultyLevel.EASY)
    result = manager.apply_difficulty_multiplier(20, "durability_change")
    assert result == 10.0, "应用难度系数失败"
    print(f"   [OK] 应用难度系数: 20 x 0.5 = {result}")
    
    print("\n[OK] M3.4 游戏难度参数系统测试通过")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("M3 核心业务逻辑层测试")
    print("=" * 60)
    
    try:
        test_forgotten_curve()
        test_durability()
        test_realm_unlock()
        test_difficulty()
        
        print("\n" + "=" * 60)
        print("[OK] 所有测试通过！")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

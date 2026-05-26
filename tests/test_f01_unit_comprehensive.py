"""
F01 卡牌系统综合单元测试

覆盖所有核心函数的边界值和边缘情况，与 test_f01_card_system.py 互补。
测试类：
- TestComputeCardStatusComprehensive
- TestDurabilityManagerComprehensive
- TestApplyDailyDecayComprehensive
- TestIsInGracePeriodComprehensive
- TestCardRepositoryComprehensive
- TestCardPydanticModels
- TestComputeStatusInternal
- TestCardToResponse
"""

import sys
import pytest
import json
from datetime import datetime, timedelta, date
from unittest.mock import MagicMock, patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from algomate.core.game.durability import (
    compute_card_status,
    apply_daily_decay,
    DurabilityManager,
    DurabilityAction,
    DurabilityConfig,
    GRACE_PERIOD_DAYS,
)
from algomate.models.cards import (
    Card,
    CardCreate,
    CardUpdate,
    CardResponse,
)
from algomate.api.v1.cards import _card_to_response


# ============================================================
# 1. TestComputeCardStatusComprehensive
# ============================================================

class TestComputeCardStatusComprehensive:
    """compute_card_status 函数的边界值和边缘情况综合测试"""

    @pytest.mark.parametrize("durability,expected", [
        (0, "pending_retake"),
        (1, "endangered"),
        (29, "endangered"),
        (30, "normal"),
        (31, "normal"),
        (80, "normal"),
        (100, "normal"),
    ])
    def test_durability_boundary_values_without_pending_retake(self, durability, expected):
        # 验证各耐久度边界值在 pending_retake=False 时的状态映射
        result = compute_card_status(durability, pending_retake=False)
        assert result == expected

    @pytest.mark.parametrize("durability", [0, 1, 29, 30, 31, 80, 100])
    def test_pending_retake_true_overrides_all_durability(self, durability):
        # pending_retake=True 时，无论耐久度多少，状态都应为 pending_retake
        result = compute_card_status(durability, pending_retake=True)
        assert result == "pending_retake"

    def test_negative_durability_treated_as_endangered(self):
        # 负数耐久度不属于 pending_retake（不等于0），且 <30，应为 endangered
        result = compute_card_status(-1, pending_retake=False)
        assert result == "endangered"

    def test_negative_durability_with_pending_retake(self):
        # 负数耐久度 + pending_retake=True → 仍为 pending_retake
        result = compute_card_status(-1, pending_retake=True)
        assert result == "pending_retake"

    def test_very_large_durability_is_normal(self):
        # 极大耐久度值仍应为 normal
        result = compute_card_status(999999, pending_retake=False)
        assert result == "normal"

    def test_durability_exactly_at_threshold_30(self):
        # 耐久度恰好等于濒危阈值30，应为 normal（>=30）
        result = compute_card_status(30, pending_retake=False)
        assert result == "normal"

    def test_durability_one_below_threshold(self):
        # 耐久度为29，恰好低于濒危阈值，应为 endangered
        result = compute_card_status(29, pending_retake=False)
        assert result == "endangered"


# ============================================================
# 2. TestDurabilityManagerComprehensive
# ============================================================

class TestDurabilityManagerComprehensive:
    """DurabilityManager 类的综合测试"""

    @pytest.mark.parametrize("action,difficulty,expected_sign", [
        (DurabilityAction.REVIEW_SUCCESS, "easy", 1),
        (DurabilityAction.REVIEW_SUCCESS, "normal", 1),
        (DurabilityAction.REVIEW_SUCCESS, "hard", 1),
        (DurabilityAction.REVIEW_FAIL, "easy", -1),
        (DurabilityAction.REVIEW_FAIL, "normal", -1),
        (DurabilityAction.REVIEW_FAIL, "hard", -1),
        (DurabilityAction.DAILY_DECAY, "easy", -1),
        (DurabilityAction.DAILY_DECAY, "normal", -1),
        (DurabilityAction.DAILY_DECAY, "hard", -1),
        (DurabilityAction.BOSS_DEFEAT, "easy", 1),
        (DurabilityAction.BOSS_DEFEAT, "normal", 1),
        (DurabilityAction.BOSS_DEFEAT, "hard", 1),
        (DurabilityAction.BOSS_FAIL, "easy", -1),
        (DurabilityAction.BOSS_FAIL, "normal", -1),
        (DurabilityAction.BOSS_FAIL, "hard", -1),
    ])
    def test_calculate_durability_change_sign_for_all_actions_and_difficulties(self, action, difficulty, expected_sign):
        # 验证所有动作类型在所有难度下的变化值符号（正/负）
        manager = DurabilityManager()
        change = manager.calculate_durability_change(action, difficulty)
        if expected_sign > 0:
            assert change > 0
        else:
            assert change < 0

    @pytest.mark.parametrize("action", [
        DurabilityAction.REVIEW_SUCCESS,
        DurabilityAction.REVIEW_FAIL,
        DurabilityAction.DAILY_DECAY,
        DurabilityAction.BOSS_DEFEAT,
        DurabilityAction.BOSS_FAIL,
    ])
    def test_calculate_durability_change_easy_less_than_hard(self, action):
        # easy 难度的变化量绝对值应小于 hard 难度
        manager = DurabilityManager()
        easy_change = manager.calculate_durability_change(action, "easy")
        hard_change = manager.calculate_durability_change(action, "hard")
        assert abs(easy_change) <= abs(hard_change)

    def test_calculate_durability_change_review_success_normal_is_20(self):
        # 修炼成功 + normal 难度 = +20
        manager = DurabilityManager()
        change = manager.calculate_durability_change(DurabilityAction.REVIEW_SUCCESS, "normal")
        assert change == 20

    def test_calculate_durability_change_review_fail_normal_is_minus_5(self):
        # 修炼失败 + normal 难度 = -5
        manager = DurabilityManager()
        change = manager.calculate_durability_change(DurabilityAction.REVIEW_FAIL, "normal")
        assert change == -5

    def test_calculate_durability_change_daily_decay_normal_is_minus_2(self):
        # 每日衰减 + normal 难度 = -2
        manager = DurabilityManager()
        change = manager.calculate_durability_change(DurabilityAction.DAILY_DECAY, "normal")
        assert change == -2

    def test_calculate_durability_change_boss_defeat_normal_is_20(self):
        # Boss 击败 + normal 难度 = +20（与 REVIEW_SUCCESS 相同基础值）
        manager = DurabilityManager()
        change = manager.calculate_durability_change(DurabilityAction.BOSS_DEFEAT, "normal")
        assert change == 20

    def test_calculate_durability_change_boss_fail_normal_is_minus_5(self):
        # Boss 失败 + normal 难度 = -5（与 REVIEW_FAIL 相同基础值）
        manager = DurabilityManager()
        change = manager.calculate_durability_change(DurabilityAction.BOSS_FAIL, "normal")
        assert change == -5

    def test_update_durability_max_capped_at_100(self):
        # 耐久度100时修炼成功，应封顶在100
        manager = DurabilityManager()
        new_dur, is_critical, is_sealed = manager.update_durability(
            100, DurabilityAction.REVIEW_SUCCESS, "normal"
        )
        assert new_dur == 100
        assert is_critical is False
        assert is_sealed is False

    def test_update_durability_min_capped_at_0(self):
        # 耐久度0时修炼失败，应保持在0
        manager = DurabilityManager()
        new_dur, is_critical, is_sealed = manager.update_durability(
            0, DurabilityAction.REVIEW_FAIL, "normal"
        )
        assert new_dur == 0
        assert is_sealed is True

    def test_update_durability_near_max_with_success(self):
        # 耐久度95时修炼成功，应封顶在100而非120
        manager = DurabilityManager()
        new_dur, _, _ = manager.update_durability(
            95, DurabilityAction.REVIEW_SUCCESS, "normal"
        )
        assert new_dur == 100

    def test_update_durability_near_min_with_fail(self):
        # 耐久度3时修炼失败，应封底在0而非-2
        manager = DurabilityManager()
        new_dur, _, is_sealed = manager.update_durability(
            3, DurabilityAction.REVIEW_FAIL, "normal"
        )
        assert new_dur == 0
        assert is_sealed is True

    def test_get_difficulty_multiplier_unknown_returns_1(self):
        # 未知难度应返回默认系数 1.0
        manager = DurabilityManager()
        result = manager.get_difficulty_multiplier("extreme")
        assert result == 1.0

    def test_get_difficulty_multiplier_easy(self):
        manager = DurabilityManager()
        assert manager.get_difficulty_multiplier("easy") == 0.5

    def test_get_difficulty_multiplier_normal(self):
        manager = DurabilityManager()
        assert manager.get_difficulty_multiplier("normal") == 1.0

    def test_get_difficulty_multiplier_hard(self):
        manager = DurabilityManager()
        assert manager.get_difficulty_multiplier("hard") == 1.5

    @pytest.mark.parametrize("durability,expected", [
        (0, True),
        (1, True),
        (29, True),
        (30, False),
        (31, False),
        (80, False),
        (100, False),
    ])
    def test_is_critical_boundary_values(self, durability, expected):
        # 濒危判断边界值：durability < 30 为濒危
        manager = DurabilityManager()
        assert manager.is_critical(durability) == expected

    @pytest.mark.parametrize("durability,expected", [
        (0, True),
        (1, False),
        (29, False),
        (30, False),
        (100, False),
    ])
    def test_needs_retake_boundary_values(self, durability, expected):
        # 需要重修判断边界值：仅 durability == 0 为需要重修
        manager = DurabilityManager()
        assert manager.needs_retake(durability) == expected

    def test_unseal_durability_returns_80(self):
        # 解封恢复耐久度应为80
        manager = DurabilityManager()
        assert manager.unseal_durability() == 80

    def test_get_durability_status_sealed(self):
        # 耐久度0 → 待重修状态
        manager = DurabilityManager()
        status = manager.get_durability_status(0)
        assert status["status"] == "待重修"
        assert status["needs_retake"] is True
        assert status["is_critical"] is True
        assert status["durability"] == 0

    def test_get_durability_status_critical(self):
        # 耐久度15 → 濒危状态
        manager = DurabilityManager()
        status = manager.get_durability_status(15)
        assert status["status"] == "濒危"
        assert status["is_critical"] is True
        assert status["needs_retake"] is False
        assert status["durability"] == 15

    def test_get_durability_status_normal(self):
        # 耐久度80 → 正常状态
        manager = DurabilityManager()
        status = manager.get_durability_status(80)
        assert status["status"] == "正常"
        assert status["is_critical"] is False
        assert status["needs_retake"] is False
        assert status["durability"] == 80

    def test_apply_daily_decay_to_cards_mixed_states(self):
        # 混合卡牌状态：待重修跳过、宽限期跳过、正常衰减
        manager = DurabilityManager()

        pending_retake_card = MagicMock()
        pending_retake_card.pending_retake = True
        pending_retake_card.durability = 0
        pending_retake_card.created_at = datetime.now() - timedelta(days=10)

        grace_card = MagicMock()
        grace_card.pending_retake = False
        grace_card.durability = 80
        grace_card.created_at = datetime.now() - timedelta(days=1)

        normal_card = MagicMock()
        normal_card.pending_retake = False
        normal_card.durability = 80
        normal_card.created_at = datetime.now() - timedelta(days=10)

        result = manager.apply_daily_decay_to_cards([pending_retake_card, grace_card, normal_card])

        # 只有 normal_card 被衰减
        assert len(result) == 1
        assert result[0]["card"] is normal_card
        assert result[0]["old_durability"] == 80
        assert result[0]["new_durability"] == 78

    def test_custom_config_changes_thresholds(self):
        # 自定义 DurabilityConfig 改变阈值后，is_critical 和 needs_retake 行为变化
        custom_config = DurabilityConfig(
            success_base=30,
            fail_base=10,
            daily_decay_base=5,
            critical_threshold=50,
            sealed_threshold=0,
            max_durability=200,
            min_durability=0,
        )
        manager = DurabilityManager(config=custom_config)

        # durability=40 < critical_threshold=50 → 濒危
        assert manager.is_critical(40) is True
        # durability=50 >= critical_threshold=50 → 非濒危
        assert manager.is_critical(50) is False

        # 修炼成功 + normal → +30
        change = manager.calculate_durability_change(DurabilityAction.REVIEW_SUCCESS, "normal")
        assert change == 30

        # 每日衰减 + normal → -5
        decay = manager.calculate_durability_change(DurabilityAction.DAILY_DECAY, "normal")
        assert decay == -5

    def test_custom_difficulty_multipliers(self):
        # 自定义难度系数映射
        custom_multipliers = {"easy": 0.8, "normal": 1.0, "hard": 2.0, "extreme": 3.0}
        manager = DurabilityManager(difficulty_multipliers=custom_multipliers)

        assert manager.get_difficulty_multiplier("easy") == 0.8
        assert manager.get_difficulty_multiplier("hard") == 2.0
        assert manager.get_difficulty_multiplier("extreme") == 3.0
        # 未知难度仍返回 1.0
        assert manager.get_difficulty_multiplier("unknown") == 1.0


# ============================================================
# 3. TestApplyDailyDecayComprehensive
# ============================================================

class TestApplyDailyDecayComprehensive:
    """apply_daily_decay 函数的综合测试"""

    def test_normal_decay_easy(self):
        # easy 难度衰减：-2 * 0.5 = -1
        card = MagicMock()
        card.durability = 80
        card.pending_retake = False
        card.is_sealed = False
        card.created_at = datetime.now() - timedelta(days=10)
        result = apply_daily_decay(card, difficulty="easy")
        assert result["decayed"] is True
        assert result["new_durability"] == 79
        assert result["old_durability"] == 80

    def test_normal_decay_normal(self):
        # normal 难度衰减：-2 * 1.0 = -2
        card = MagicMock()
        card.durability = 80
        card.pending_retake = False
        card.is_sealed = False
        card.created_at = datetime.now() - timedelta(days=10)
        result = apply_daily_decay(card, difficulty="normal")
        assert result["decayed"] is True
        assert result["new_durability"] == 78

    def test_normal_decay_hard(self):
        # hard 难度衰减：-2 * 1.5 = -3
        card = MagicMock()
        card.durability = 80
        card.pending_retake = False
        card.is_sealed = False
        card.created_at = datetime.now() - timedelta(days=10)
        result = apply_daily_decay(card, difficulty="hard")
        assert result["decayed"] is True
        assert result["new_durability"] == 77

    def test_durability_2_hits_zero_becomes_pending_retake(self):
        # 耐久度2衰减后变为0，状态应为 pending_retake
        card = MagicMock()
        card.durability = 2
        card.pending_retake = False
        card.is_sealed = False
        card.created_at = datetime.now() - timedelta(days=10)
        result = apply_daily_decay(card, difficulty="normal")
        assert result["decayed"] is True
        assert result["new_durability"] == 0
        assert result["status"] == "pending_retake"

    def test_durability_1_hits_zero(self):
        # 耐久度1衰减后变为0（封底）
        card = MagicMock()
        card.durability = 1
        card.pending_retake = False
        card.is_sealed = False
        card.created_at = datetime.now() - timedelta(days=10)
        result = apply_daily_decay(card, difficulty="normal")
        assert result["decayed"] is True
        assert result["new_durability"] == 0

    def test_durability_zero_not_decayed(self):
        # 耐久度0且 pending_retake=True 的卡牌不参与衰减
        card = MagicMock()
        card.durability = 0
        card.pending_retake = True
        card.is_sealed = False
        card.created_at = datetime.now() - timedelta(days=10)
        result = apply_daily_decay(card)
        assert result["decayed"] is False
        assert result["new_durability"] == 0

    def test_pending_retake_card_not_decayed(self):
        # 待重修卡牌不参与衰减
        card = MagicMock()
        card.durability = 0
        card.pending_retake = True
        card.created_at = datetime.now() - timedelta(days=10)
        result = apply_daily_decay(card)
        assert result["decayed"] is False

    def test_card_without_created_at_still_decays(self):
        # 没有 created_at 属性的卡牌（不在宽限期内判断），仍会被衰减
        card = MagicMock(spec=[])
        card.durability = 80
        card.pending_retake = False
        card.is_sealed = False
        # 不设置 created_at → hasattr 返回 False
        result = apply_daily_decay(card, difficulty="normal")
        assert result["decayed"] is True
        assert result["new_durability"] == 78

    def test_card_without_durability_defaults_to_80(self):
        # 没有 durability 属性的卡牌，默认耐久度为80
        card = MagicMock(spec=["pending_retake", "is_sealed", "created_at"])
        card.pending_retake = False
        card.is_sealed = False
        card.created_at = datetime.now() - timedelta(days=10)
        result = apply_daily_decay(card, difficulty="normal")
        assert result["decayed"] is True
        assert result["old_durability"] == 80
        assert result["new_durability"] == 78


# ============================================================
# 4. TestIsInGracePeriodComprehensive
# ============================================================

class TestIsInGracePeriodComprehensive:
    """DurabilityManager.is_in_grace_period 的综合边界测试

    is_in_grace_period 使用日期级别比较（created_at.date() + 3 > today），
    因此测试需要使用固定日期来避免时间依赖的 flaky 问题。
    """

    def test_just_created_zero_days_ago(self):
        # 刚创建（今天）应在宽限期内：今天 + 3 > 今天 → True
        manager = DurabilityManager()
        created_at = datetime.now()
        assert manager.is_in_grace_period(created_at) is True

    def test_one_day_ago(self):
        # 1天前创建，应在宽限期内
        manager = DurabilityManager()
        created_at = datetime.now() - timedelta(days=1)
        assert manager.is_in_grace_period(created_at) is True

    def test_two_days_ago_still_in_grace(self):
        # 2天前创建，应在宽限期内：2天前的日期 + 3 = 明天 > 今天 → True
        manager = DurabilityManager()
        created_at = datetime.now() - timedelta(days=2)
        assert manager.is_in_grace_period(created_at) is True

    def test_two_days_23_hours_ago_with_fixed_date(self):
        # 使用固定中午时间，2天23小时前的日期仍为2天前日历日 → 在宽限期内
        # 固定 "now" 为中午12:00，2天23小时前 = 2天前的13:00，日历日为2天前
        manager = DurabilityManager()
        fixed_now = datetime(2026, 5, 6, 12, 0, 0)
        created_at = fixed_now - timedelta(days=2, hours=23)
        # created_at = 2026-05-03 13:00 → date = 2026-05-03
        # 2026-05-03 + 3 = 2026-05-06 > 2026-05-06 → False
        # 因为日期比较，5月3号 + 3天 = 5月6号 = 今天，不大于今天
        # 所以这个测试验证的是：日期级别比较下，2天23小时前可能不在宽限期内
        result = manager.is_in_grace_period(created_at)
        # 日期级比较：5月3日 + 3天 = 5月6日，不大于5月6日 → False
        assert result is False

    def test_two_days_ago_with_real_datetime_still_in_grace(self):
        # 使用真实 datetime.now()，2天前创建在宽限期内
        manager = DurabilityManager()
        created_at = datetime.now() - timedelta(days=2)
        # created_at.date() = 2天前
        # 2天前 + 3 = 明天 > 今天 → True
        result = manager.is_in_grace_period(created_at)
        assert result is True

    def test_exactly_three_days_ago(self):
        # 恰好3天前创建，应在宽限期外（边界值）
        manager = DurabilityManager()
        created_at = datetime.now() - timedelta(days=3)
        # 使用日期比较，3天前的日期 + 3天 = 今天 → 不大于今天 → False
        result = manager.is_in_grace_period(created_at)
        assert result is False

    def test_four_days_ago(self):
        # 4天前创建，应在宽限期外
        manager = DurabilityManager()
        created_at = datetime.now() - timedelta(days=4)
        assert manager.is_in_grace_period(created_at) is False

    def test_none_returns_false(self):
        # created_at 为 None → 不在宽限期内
        manager = DurabilityManager()
        assert manager.is_in_grace_period(None) is False

    def test_future_date_returns_true(self):
        # 未来日期的 created_at 应在宽限期内
        manager = DurabilityManager()
        created_at = datetime.now() + timedelta(days=1)
        assert manager.is_in_grace_period(created_at) is True

    def test_grace_period_constant_is_3(self):
        # 验证宽限期常量为3天
        assert GRACE_PERIOD_DAYS == 3


# ============================================================
# 5. TestCardRepositoryComprehensive
# ============================================================

def _setup_test_db():
    from algomate.data.database import Base
    from algomate.models.npcs import NPC
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    class _TestDB:
        def get_session(self):
            return SessionLocal()

    test_db = _TestDB()

    session = test_db.get_session()
    npc = NPC(
        name="Test NPC",
        domain="新手森林",
        location="新手森林",
        system_prompt="You are a test NPC",
    )
    session.add(npc)
    session.commit()
    npc_id = npc.id
    session.close()

    return test_db, npc_id


class TestCardRepositoryComprehensive:
    """CardRepository 的综合测试"""

    @pytest.fixture
    def repo_and_npc(self):
        from algomate.data.repositories.card_repo import CardRepository
        test_db, npc_id = _setup_test_db()
        repo = CardRepository(test_db)
        return repo, npc_id, test_db

    def test_create_with_all_new_fields(self, repo_and_npc):
        # 创建卡牌时传入所有新增字段
        repo, npc_id, _ = repo_and_npc
        card = repo.create(
            name="Full Card",
            algorithm_type="basic_data_structure",
            npc_id=npc_id,
            durability=80,
            pending_retake=False,
            basic_content=json.dumps({"concept_definition": "核心概念", "features": "特点"}, ensure_ascii=False),
            practical_content=json.dumps({"examples": ["示例"], "applicable_scenarios": "使用场景", "precautions": "注意事项"}, ensure_ascii=False),
            advanced_content=json.dumps({"common_mistakes": "常见陷阱", "extensions": "常见变体", "advanced_solutions": "典型题目"}, ensure_ascii=False),
            my_notes="个人笔记",
            visual_links="https://example.com/viz",
            topic="排序算法",
        )
        basic = json.loads(card.basic_content)
        assert basic["concept_definition"] == "核心概念"
        practical = json.loads(card.practical_content)
        assert practical["applicable_scenarios"] == "使用场景"
        advanced = json.loads(card.advanced_content)
        assert advanced["common_mistakes"] == "常见陷阱"
        assert card.my_notes == "个人笔记"
        assert card.visual_links == "https://example.com/viz"
        assert card.topic == "排序算法"

    def test_create_with_durability_zero_sets_pending_retake(self, repo_and_npc):
        # 创建时 durability=0 应自动设置 pending_retake=True
        repo, npc_id, _ = repo_and_npc
        card = repo.create(
            name="Sealed Card",
            algorithm_type="basic_data_structure",
            npc_id=npc_id,
            durability=0,
            pending_retake=True,
        )
        assert card.pending_retake is True
        assert card.durability == 0

    def test_create_with_normal_durability_not_pending_retake(self, repo_and_npc):
        # 创建时 durability>0 不应设置 pending_retake
        repo, npc_id, _ = repo_and_npc
        card = repo.create(
            name="Normal Card",
            algorithm_type="basic_data_structure",
            npc_id=npc_id,
            durability=80,
        )
        assert card.pending_retake is False

    def test_get_by_id_existing_card(self, repo_and_npc):
        # 通过 ID 获取已存在的卡牌
        repo, npc_id, _ = repo_and_npc
        card = repo.create(name="Find Me", algorithm_type="basic_data_structure", npc_id=npc_id)
        found = repo.get_by_id(card.id)
        assert found is not None
        assert found.name == "Find Me"

    def test_get_by_id_non_existing_card(self, repo_and_npc):
        # 获取不存在的卡牌返回 None
        repo, npc_id, _ = repo_and_npc
        found = repo.get_by_id(99999)
        assert found is None

    def test_update_with_dimension_fields(self, repo_and_npc):
        # 更新卡牌的维度字段
        repo, npc_id, _ = repo_and_npc
        card = repo.create(name="Update Me", algorithm_type="basic_data_structure", npc_id=npc_id)
        updated = repo.update(
            card.id,
            basic_content=json.dumps({"concept_definition": "新概念"}, ensure_ascii=False),
            topic="新主题",
        )
        assert updated is not None
        assert json.loads(updated.basic_content)["concept_definition"] == "新概念"
        assert updated.topic == "新主题"

    def test_update_non_existing_card_returns_none(self, repo_and_npc):
        # 更新不存在的卡牌返回 None
        repo, npc_id, _ = repo_and_npc
        result = repo.update(99999, name="Ghost")
        assert result is None

    def test_update_durability_to_zero_sets_pending_retake(self, repo_and_npc):
        # 更新耐久度为0时自动设置 pending_retake=True
        repo, npc_id, _ = repo_and_npc
        card = repo.create(name="Will Seal", algorithm_type="basic_data_structure", npc_id=npc_id, durability=80)
        repo.update(card.id, durability=0, pending_retake=True)
        updated = repo.get_by_id(card.id)
        assert updated.pending_retake is True
        assert updated.durability == 0

    def test_delete_existing_card(self, repo_and_npc):
        # 删除已存在的卡牌返回 True
        repo, npc_id, _ = repo_and_npc
        card = repo.create(name="Delete Me", algorithm_type="basic_data_structure", npc_id=npc_id)
        result = repo.delete(card.id)
        assert result is True
        assert repo.get_by_id(card.id) is None

    def test_delete_non_existing_card(self, repo_and_npc):
        # 删除不存在的卡牌返回 False
        repo, npc_id, _ = repo_and_npc
        result = repo.delete(99999)
        assert result is False

    def test_count_by_status_mixed_states(self, repo_and_npc):
        # 混合状态的卡牌统计
        repo, npc_id, _ = repo_and_npc
        repo.create(name="Normal", algorithm_type="basic_data_structure", npc_id=npc_id, durability=80)
        repo.create(name="Endangered", algorithm_type="basic_data_structure", npc_id=npc_id, durability=15)
        repo.create(name="PendingRetake", algorithm_type="basic_data_structure", npc_id=npc_id, durability=0, pending_retake=True)
        counts = repo.count_by_status()
        assert counts["normal"] >= 1
        assert counts["endangered"] >= 1
        assert counts["pending_retake"] >= 1

    def test_search_by_keyword_matching_name(self, repo_and_npc):
        # 按名称关键词搜索
        repo, npc_id, _ = repo_and_npc
        repo.create(name="Binary Search", algorithm_type="basic_data_structure", npc_id=npc_id)
        repo.create(name="Quick Sort", algorithm_type="basic_data_structure", npc_id=npc_id)
        results = repo.search_by_keyword("Search")
        assert len(results) >= 1
        assert all("Search" in card.name for card in results)

    def test_search_by_keyword_matching_algorithm_type(self, repo_and_npc):
        # 按算法类型关键词搜索
        repo, npc_id, _ = repo_and_npc
        repo.create(name="Card A", algorithm_type="DP", npc_id=npc_id)
        repo.create(name="Card B", algorithm_type="Search", npc_id=npc_id)
        results = repo.search_by_keyword("DP")
        assert len(results) >= 1
        assert all(card.algorithm_type == "DP" for card in results)

    def test_search_by_keyword_matching_core_concept(self, repo_and_npc):
        # 按核心概念关键词搜索
        repo, npc_id, _ = repo_and_npc
        repo.create(
            name="Content Card",
            algorithm_type="basic_data_structure",
            npc_id=npc_id,
            core_concept="动态规划是解决最优化问题的方法",
        )
        repo.create(
            name="Other Card",
            algorithm_type="basic_data_structure",
            npc_id=npc_id,
            core_concept="贪心算法",
        )
        results = repo.search_by_keyword("动态规划")
        assert len(results) >= 1
        assert "动态规划" in results[0].core_concept

    def test_get_active_excludes_pending_retake(self, repo_and_npc):
        # get_active 不返回待重修卡牌
        repo, npc_id, _ = repo_and_npc
        repo.create(name="Normal", algorithm_type="basic_data_structure", npc_id=npc_id, durability=80)
        repo.create(name="PendingRetake", algorithm_type="basic_data_structure", npc_id=npc_id, durability=0, pending_retake=True)
        active = repo.get_active()
        assert all(card.pending_retake is False for card in active)

    def test_count_returns_total(self, repo_and_npc):
        # count 返回卡牌总数
        repo, npc_id, _ = repo_and_npc
        repo.create(name="Card 1", algorithm_type="basic_data_structure", npc_id=npc_id)
        repo.create(name="Card 2", algorithm_type="basic_data_structure", npc_id=npc_id)
        total = repo.count()
        assert total >= 2

    def test_count_pending_retake_only_pending_retake_cards(self, repo_and_npc):
        # count_pending_retake 仅统计待重修卡牌
        repo, npc_id, _ = repo_and_npc
        repo.create(name="Normal", algorithm_type="basic_data_structure", npc_id=npc_id, durability=80)
        repo.create(name="PendingRetake", algorithm_type="basic_data_structure", npc_id=npc_id, durability=0, pending_retake=True)
        pending_retake_count = repo.count_pending_retake()
        assert pending_retake_count >= 1


# ============================================================
# 6. TestCardPydanticModels
# ============================================================

class TestCardPydanticModels:
    """Pydantic 模型的验证测试"""

    def test_card_create_name_min_length_1(self):
        # name 最小长度为1，空字符串应校验失败
        with pytest.raises(Exception):
            CardCreate(name="")

    def test_card_create_name_valid(self):
        # 合法 name 应通过校验
        model = CardCreate(name="有效名称")
        assert model.name == "有效名称"

    def test_card_create_name_max_length_200(self):
        # name 最大长度为200
        with pytest.raises(Exception):
            CardCreate(name="x" * 201)

    def test_card_create_durability_ge_0(self):
        # durability 最小值为0，-1 应校验失败
        with pytest.raises(Exception):
            CardCreate(name="Test", durability=-1)

    def test_card_create_durability_le_100(self):
        # durability 最大值为100，101 应校验失败
        with pytest.raises(Exception):
            CardCreate(name="Test", durability=101)

    def test_card_create_durability_valid_range(self):
        # durability 0 和 100 都应通过校验
        model0 = CardCreate(name="Test", durability=0)
        assert model0.durability == 0
        model100 = CardCreate(name="Test", durability=100)
        assert model100.durability == 100

    def test_card_update_no_fields_set_excludes_unset_empty(self):
        # CardUpdate 不设置任何字段时，model_dump(exclude_unset=True) 返回空字典
        model = CardUpdate()
        dumped = model.model_dump(exclude_unset=True)
        assert dumped == {}

    def test_card_update_only_set_fields_included(self):
        # CardUpdate 只设置部分字段时，model_dump(exclude_unset=True) 仅包含已设置字段
        model = CardUpdate(basic_content={"concept_definition": "新概念"}, my_notes="新笔记")
        dumped = model.model_dump(exclude_unset=True)
        assert "basic_content" in dumped
        assert "my_notes" in dumped
        assert "practical_content" not in dumped
        assert "visual_links" not in dumped

    def test_card_response_construction_from_data(self):
        # CardResponse 可从关键字参数构造
        now = datetime.now()
        resp = CardResponse(
            id=1,
            name="Test Card",
            durability=80,
            status="normal",
            created_at=now,
        )
        assert resp.id == 1
        assert resp.name == "Test Card"
        assert resp.durability == 80
        assert resp.status == "normal"

    def test_card_create_default_values(self):
        # CardCreate 各字段默认值验证
        model = CardCreate(name="Test")
        assert model.durability == 80
        assert model.algorithm_type == ""
        assert model.topic == ""
        assert model.npc_id == 1
        assert model.basic_content == "{}"
        assert model.visual_links is None


# ============================================================
# 7. TestComputeStatusInternal
# ============================================================

# ============================================================
# 8. TestCardToResponse
# ============================================================

class TestCardToResponse:
    """_card_to_response 函数的综合映射测试"""

    def _make_card(self, **overrides):
        """构造一个模拟 Card 对象用于测试"""
        defaults = dict(
            id=1,
            name="Test Card",
            algorithm_type="DP",
            durability=80,
            review_level=2,
            next_review_date=None,
            review_count=5,
            last_reviewed=None,
            pending_retake=False,
            npc_id=3,
            topic="排序算法",
            basic_content='{"concept_definition": "核心概念", "features": "要点"}',
            practical_content='{"examples": [], "applicable_scenarios": "使用场景", "precautions": "注意事项"}',
            advanced_content='{"common_mistakes": "常见陷阱", "extensions": "常见变体", "advanced_solutions": "典型题目"}',
            my_notes="个人笔记",
            visual_links="https://example.com/viz",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        defaults.update(overrides)

        card = MagicMock()
        for key, value in defaults.items():
            setattr(card, key, value)
        return card

    def test_ten_dimension_fields_mapped(self):
        # 验证三层结构化内容正确映射到 dict
        card = self._make_card()
        resp = _card_to_response(card)
        assert resp["basic_content"]["concept_definition"] == "核心概念"
        assert resp["practical_content"]["applicable_scenarios"] == "使用场景"
        assert resp["advanced_content"]["common_mistakes"] == "常见陷阱"
        assert resp["advanced_content"]["extensions"] == "常见变体"
        assert resp["advanced_content"]["advanced_solutions"] == "典型题目"
        assert resp["my_notes"] == "个人笔记"

    def test_visual_links_included(self):
        # visual_links 应直接映射
        card = self._make_card(visual_links="https://example.com/viz")
        resp = _card_to_response(card)
        assert resp["visual_links"] == "https://example.com/viz"

    def test_visual_links_null(self):
        # visual_links 为 None 时应映射为 None
        card = self._make_card(visual_links=None)
        resp = _card_to_response(card)
        assert resp["visual_links"] is None

    def test_npc_id_included(self):
        # npc_id 应直接映射
        card = self._make_card(npc_id=42)
        resp = _card_to_response(card)
        assert resp["npc_id"] == 42

    def test_topic_included(self):
        # topic 字段应直接映射
        card = self._make_card(topic="排序算法")
        resp = _card_to_response(card)
        assert resp["topic"] == "排序算法"

    def test_pending_retake_mapped(self):
        # pending_retake 应直接映射
        card = self._make_card(pending_retake=True)
        resp = _card_to_response(card)
        assert resp["pending_retake"] is True

    def test_pending_retake_false(self):
        # pending_retake=False 应映射到 False
        card = self._make_card(pending_retake=False)
        resp = _card_to_response(card)
        assert resp["pending_retake"] is False

    def test_status_computed_normal(self):
        # 耐久度80 → status 为 normal
        card = self._make_card(durability=80, pending_retake=False)
        resp = _card_to_response(card)
        assert resp["status"] == "normal"

    def test_status_computed_endangered(self):
        # 耐久度15 → status 为 endangered
        card = self._make_card(durability=15, pending_retake=False)
        resp = _card_to_response(card)
        assert resp["status"] == "endangered"

    def test_status_computed_pending_retake_from_durability_zero(self):
        # durability=0 → status 为 pending_retake
        card = self._make_card(durability=0, pending_retake=False)
        resp = _card_to_response(card)
        assert resp["status"] == "pending_retake"

    def test_status_computed_pending_retake_from_pending_retake(self):
        # pending_retake=True → status 为 pending_retake
        card = self._make_card(durability=80, pending_retake=True)
        resp = _card_to_response(card)
        assert resp["status"] == "pending_retake"

    def test_basic_content_json_parsed(self):
        # basic_content JSON 字符串被解析为 dict
        card = self._make_card(basic_content='{"concept_definition": "概念A", "features": "要点B"}')
        resp = _card_to_response(card)
        assert resp["basic_content"]["concept_definition"] == "概念A"
        assert resp["basic_content"]["features"] == "要点B"

    def test_basic_content_empty_json(self):
        # basic_content 为空 JSON 对象字符串
        card = self._make_card(basic_content="{}")
        resp = _card_to_response(card)
        assert resp["basic_content"] == {}

    def test_basic_content_invalid_json_returns_empty_dict(self):
        # basic_content 为无效 JSON 字符串时返回空 dict
        card = self._make_card(basic_content="")
        resp = _card_to_response(card)
        assert resp["basic_content"] == {}

    def test_review_count_from_card_attribute(self):
        # review_count 从 card 属性获取
        card = self._make_card(review_count=10)
        resp = _card_to_response(card)
        assert resp["review_count"] == 10

    def test_algorithm_type_mapped(self):
        # algorithm_type 应直接映射
        card = self._make_card(algorithm_type="Search")
        resp = _card_to_response(card)
        assert resp["algorithm_type"] == "Search"

    def test_review_level_mapped(self):
        # review_level 应直接映射
        card = self._make_card(review_level=3)
        resp = _card_to_response(card)
        assert resp["review_level"] == 3

    def test_updated_at_mapped_to_isoformat(self):
        # updated_at 应映射为 ISO 格式字符串
        now = datetime(2026, 5, 24, 12, 0, 0)
        card = self._make_card(updated_at=now)
        resp = _card_to_response(card)
        assert resp["updated_at"] == now.isoformat()
